import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from layer_formulas import (
    calculate_layer_capacity,
    calculate_capacity_curve,
    parse_layer_lines
)


def run_app():
    results = []

    def import_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV file", "*.csv")])
        if not file_path:
            return

        layer_text.delete("1.0", tk.END)

        with open(file_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                layer_text.insert(
                    tk.END,
                    f'{row["from_depth"]},{row["to_depth"]},{row["soil_type"]},{row["behavior"]},'
                    f'{row["gamma"]},{row["cu"]},{row["qc_f"]},{row["qc_eb"]},{row["delta_cv"]},'
                    f'{row["k0"]},{row["flim"]},{row["qlim"]}\n'
                )

    def apply_pile_case(event=None):
        case = pile_case_combo.get()

        if case == "54-in OD":
            entry_diameter.delete(0, tk.END)
            entry_diameter.insert(0, "1.3716")

            entry_length.delete(0, tk.END)
            entry_length.insert(0, "173.563")

            entry_analysis_depth.delete(0, tk.END)
            entry_analysis_depth.insert(0, "157.5")

            entry_wt.delete(0, tk.END)
            entry_wt.insert(0, "0.0445")

        elif case == "66-in OD":
            entry_diameter.delete(0, tk.END)
            entry_diameter.insert(0, "1.6764")

            entry_length.delete(0, tk.END)
            entry_length.insert(0, "171.550")

            entry_analysis_depth.delete(0, tk.END)
            entry_analysis_depth.insert(0, "157.5")

            entry_wt.delete(0, tk.END)
            entry_wt.insert(0, "0.0445")

    def calculate():
        nonlocal results
        results = []

        try:
            D = float(entry_diameter.get())
            pile_length = float(entry_length.get())
            analysis_depth = float(entry_analysis_depth.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            method = method_combo.get()
            loading_type = loading_combo.get().lower()

            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

            rows, summary, layers = calculate_layer_capacity(
                D=D,
                L=analysis_depth,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type
            )

            table.delete(*table.get_children())

            for row in rows:
                values = [
                    row["depth_range"],
                    row["soil_type"],
                    row["behavior"],
                    f'{row["gamma"]:.1f}',
                    "-" if row["cu"] is None else f'{row["cu"]:.1f}',
                    "-" if row["qc_f_mpa"] is None else f'{row["qc_f_mpa"]:.1f}',
                    "-" if row["qc_eb_mpa"] is None else f'{row["qc_eb_mpa"]:.1f}',
                    "-" if row["delta_cv"] is None else f'{row["delta_cv"]:.1f}',
                    "-" if row["k0"] is None else f'{row["k0"]:.2f}',
                    "-" if row["flim"] is None else f'{row["flim"]:.1f}',
                    "-" if row["qlim_mpa"] is None else f'{row["qlim_mpa"]:.1f}',
                    row["used_parameter"],
                    f'{row["unit_shaft"]:.2f}',
                    f'{row["qshaft_layer"]:.2f}'
                ]

                table.insert("", "end", values=values)
                results.append(values)

            qc_eb_text = "Not used / no qc_eb at pile tip"
            if summary["qc_eb_av_1_5D"] is not None:
                qc_eb_text = f'{summary["qc_eb_av_1_5D"] / 1000:.2f} MPa'

            summary_text.set(
                f"Pile Case: {pile_case_combo.get()}\n"
                f"Method: {method}\n"
                f"Loading: {summary['loading_type'].capitalize()}\n"
                f"D = {D:.4f} m\n"
                f"Pile Length = {pile_length:.3f} m\n"
                f"Analysis Depth = {analysis_depth:.3f} m\n"
                f"WT = {WT:.4f} m\n"
                f"Base model = {summary['base_model']}\n\n"
                f"Ap = {summary['Ap']:.3f} m²\n"
                f"Perimeter = {summary['perimeter']:.3f} m\n"
                f"Ar = {summary['Ar']:.3f}\n"
                f"qc_eb,av,1.5D = {qc_eb_text}\n"
                f"qbase unit = {summary['q_unit_base']:.2f} kPa\n\n"
                f"Qshaft = {summary['Qshaft']:.2f} kN\n"
                f"Qbase = {summary['Qbase']:.2f} kN\n"
                f"Qult = {summary['Qult']:.2f} kN\n"
                f"Qallow = {summary['Qallow']:.2f} kN"
            )

        except Exception as e:
            messagebox.showerror("Error", f"ข้อมูลผิดหรือกรอกไม่ครบ\n\n{e}")

    def plot_qc_profile_to_current_fig(layers):
        fig, axes = plt.subplots(
            ncols=3,
            figsize=(8.27, 11.69),
            dpi=120,
            sharey=True,
            gridspec_kw={"width_ratios": [2.2, 2.2, 1.1]}
        )

        ax_f, ax_eb, ax_soil = axes
        max_depth = max(layer["to_depth"] for layer in layers)

        qc_f_x = []
        qc_f_y = []
        qc_eb_x = []
        qc_eb_y = []

        for layer in layers:
            z1 = layer["from_depth"]
            z2 = layer["to_depth"]
            z_mid = (z1 + z2) / 2
            soil = layer["soil_type"]
            behavior = layer["behavior"]

            if layer["qc_f"] is not None:
                q = layer["qc_f"] / 1000
                qc_f_x.extend([q, q, None])
                qc_f_y.extend([z1, z2, None])

            if layer["qc_eb"] is not None:
                q = layer["qc_eb"] / 1000
                qc_eb_x.extend([q, q, None])
                qc_eb_y.extend([z1, z2, None])

            if behavior == "cohesive":
                hatch = ""
                label = "C"
            elif behavior == "frictional":
                hatch = "///"
                label = "F"
            else:
                hatch = "..."
                label = "R"

            ax_soil.fill_betweenx(
                [z1, z2],
                0.00,
                0.42,
                facecolor="white",
                edgecolor="black",
                hatch=hatch,
                linewidth=0.8
            )

            ax_soil.text(
                0.21,
                z_mid,
                label,
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold"
            )

            ax_soil.text(
                0.72,
                z_mid,
                soil.title(),
                ha="center",
                va="center",
                fontsize=6
            )

        ax_f.plot(qc_f_x, qc_f_y, color="black", linewidth=1.4)
        ax_eb.plot(qc_eb_x, qc_eb_y, color="black", linewidth=1.4)

        for ax in [ax_f, ax_eb]:
            ax.set_xlim(0, 60)
            ax.set_xticks([0, 20, 40, 60])
            ax.set_ylim(max_depth, 0)
            ax.grid(True, which="major", linestyle="-", linewidth=0.6, color="black")
            ax.tick_params(axis="both", labelsize=8)
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()

        ax_f.set_title("Cone Resistance Used for Skin Friction [MPa]", fontsize=8, pad=10)
        ax_eb.set_title("Cone Resistance Used for End Bearing [MPa]", fontsize=8, pad=10)
        ax_f.set_ylabel("Depth Below Seafloor [m]", fontsize=9)

        ax_soil.set_xlim(0, 1)
        ax_soil.set_ylim(max_depth, 0)
        ax_soil.set_xticks([])
        ax_soil.grid(True, axis="y", linestyle="-", linewidth=0.6, color="black")
        ax_soil.set_title("Ground\nBehaviour\n/\nGround\nUnit\nName", fontsize=8, pad=10)

        fig.text(
            0.5,
            0.045,
            "CONE RESISTANCE PROFILE FOR UNIT SKIN FRICTION AND UNIT END BEARING COMPUTATION",
            ha="center",
            fontsize=10,
            fontweight="bold"
        )

        fig.text(
            0.5,
            0.025,
            "DRIVEN OPEN-ENDED CIRCULAR PILE",
            ha="center",
            fontsize=8
        )

        plt.tight_layout(rect=[0.06, 0.12, 0.98, 0.95])
        return fig

    def show_report_qc_profile():
        try:
            layers = parse_layer_lines(layer_text.get("1.0", tk.END).strip().split("\n"))
            fig = plot_qc_profile_to_current_fig(layers)
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"สร้าง Report qc Profile ไม่ได้\n\n{e}")

    def make_all_methods_curve_figure(loading_type):
        D = float(entry_diameter.get())
        WT = float(entry_wt.get())
        FS = float(entry_fs.get())
        layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

        methods = [
            ("ICP-05", "API RP 2GEO - Method 1, Simplified ICP-05"),
            ("UWA-05", "API RP 2GEO - Method 2, Offshore UWA-05"),
            ("Fugro-05", "API RP 2GEO - Method 3, Fugro-05"),
            ("NGI-05", "API RP 2GEO - Method 4, NGI-05")
        ]

        fig = plt.figure(figsize=(8.27, 11.69), dpi=120)

        for method, label in methods:
            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type
            )

            if depths:
                plt.plot(qult, depths, linewidth=1.6, label=label)

        title_word = "COMPRESSION" if loading_type == "compression" else "TENSION"

        plt.gca().invert_yaxis()
        plt.xlim(0, 120)
        plt.xticks(range(0, 121, 10))
        plt.ylim(180, 0)

        plt.xlabel(f"Ultimate Axial Pile Capacity in {title_word.title()} [MN]")
        plt.ylabel("Depth Below Seafloor [m]")

        plt.title(
            f"ULTIMATE AXIAL PILE CAPACITY IN {title_word}\n"
            f"DRIVEN OPEN-ENDED CIRCULAR PILE\n"
            f"{pile_case_combo.get()}",
            fontsize=11,
            fontweight="bold"
        )

        plt.grid(True, which="major", linestyle="-", linewidth=0.6, color="black")
        plt.minorticks_on()
        plt.grid(True, which="minor", linestyle=":", linewidth=0.3)

        plt.legend(fontsize=7, loc="lower left", frameon=False)
        plt.tight_layout()
        return fig

    def show_all_methods_curve(loading_type):
        try:
            fig = make_all_methods_curve_figure(loading_type)
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"สร้าง All Methods Curve ไม่ได้\n\n{e}")

    def show_capacity_curve():
        try:
            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            method = method_combo.get()
            loading_type = loading_combo.get().lower()
            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type
            )

            if not depths:
                messagebox.showwarning("Warning", "ไม่มีข้อมูลสำหรับ Capacity Curve")
                return

            plt.figure(figsize=(8, 8), dpi=120)
            plt.plot(qult, depths, "o-", linewidth=2.4, label="Ultimate Capacity, Qult")
            plt.plot(qallow, depths, "s-", linewidth=2.4, label="Allowable Capacity, Qallow")
            plt.fill_betweenx(depths, qallow, qult, alpha=0.10, label="Safety margin")

            plt.gca().invert_yaxis()
            plt.xlabel("Axial Capacity (MN)")
            plt.ylabel("Pile Penetration Depth (m)")
            plt.title(f"{method} {loading_type.capitalize()} Capacity Curve", fontweight="bold")

            plt.grid(True, which="major", linestyle="--", linewidth=0.6, alpha=0.7)
            plt.minorticks_on()
            plt.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.4)

            plt.legend()
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"สร้าง Capacity Curve ไม่ได้\n\n{e}")

    def export_pdf_report():
        try:
            D = float(entry_diameter.get())
            pile_length = float(entry_length.get())
            analysis_depth = float(entry_analysis_depth.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
            layers = parse_layer_lines(layer_lines)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")]
            )

            if not file_path:
                return

            with PdfPages(file_path) as pdf:
                fig = plt.figure(figsize=(8.27, 11.69))
                plt.axis("off")

                text = (
                    "CPT-Based Axial Pile Capacity Report\n\n"
                    f"Pile Case: {pile_case_combo.get()}\n"
                    f"Pile Diameter, D = {D:.4f} m\n"
                    f"Pile Length = {pile_length:.3f} m\n"
                    f"Analysis Depth = {analysis_depth:.3f} m\n"
                    f"Wall Thickness, WT = {WT:.4f} m\n"
                    f"Factor of Safety = {FS:.2f}\n\n"
                    "Calculation Methods\n"
                    "- ICP-05\n"
                    "- UWA-05\n"
                    "- Fugro-05\n"
                    "- NGI-05\n\n"
                    "Notes\n"
                    "1. Cohesive Model: API RP 2GEO (2011) - Annex C (former API RP 2A - 1979)\n"
                    "2. Frictional Model: API RP 2GEO (2011) CPT-based methods\n\n"
                    "Input Parameters\n"
                    "- cu for cohesive soils\n"
                    "- qc_f for unit skin friction\n"
                    "- qc_eb for unit end bearing\n"
                    "- delta_cv, K0, flim, qlim for frictional layers\n"
                )

                plt.text(0.08, 0.95, text, va="top", fontsize=11)
                plt.title("Calculation Summary", fontsize=16, fontweight="bold")

                summary_rows = []

                for method in ["ICP-05", "UWA-05", "Fugro-05", "NGI-05"]:
                    _, comp_summary, _ = calculate_layer_capacity(
                        D=D,
                        L=analysis_depth,
                        WT=WT,
                        FS=FS,
                        method=method,
                        layer_lines=layer_lines,
                        loading_type="compression"
                    )

                    _, tens_summary, _ = calculate_layer_capacity(
                        D=D,
                        L=analysis_depth,
                        WT=WT,
                        FS=FS,
                        method=method,
                        layer_lines=layer_lines,
                        loading_type="tension"
                    )

                    summary_rows.append([
                        method,
                        f'{comp_summary["Qult"] / 1000:.2f}',
                        f'{comp_summary["Qallow"] / 1000:.2f}',
                        f'{tens_summary["Qult"] / 1000:.2f}',
                        f'{tens_summary["Qallow"] / 1000:.2f}'
                    ])

                table_data = [
                    [
                        "Method",
                        "Comp Qult\n(MN)",
                        "Comp Qallow\n(MN)",
                        "Tension Qult\n(MN)",
                        "Tension Qallow\n(MN)"
                    ]
                ] + summary_rows

                summary_table = plt.table(
                    cellText=table_data,
                    cellLoc="center",
                    bbox=[0.08, 0.08, 0.84, 0.25]
                )

                summary_table.auto_set_font_size(False)
                summary_table.set_fontsize(8)

                for key, cell in summary_table.get_celld().items():
                    cell.set_linewidth(0.8)
                    if key[0] == 0:
                        cell.set_text_props(weight="bold")

                pdf.savefig(fig)
                plt.close(fig)

                fig = plot_qc_profile_to_current_fig(layers)
                pdf.savefig(fig)
                plt.close(fig)

                fig = make_all_methods_curve_figure("compression")
                pdf.savefig(fig)
                plt.close(fig)

                fig = make_all_methods_curve_figure("tension")
                pdf.savefig(fig)
                plt.close(fig)

            messagebox.showinfo("Success", "Export PDF Report สำเร็จ")

        except Exception as e:
            messagebox.showerror("Error", f"Export PDF ไม่ได้\n\n{e}")

    def export_csv():
        if not results:
            messagebox.showwarning("Warning", "ต้องกด Calculate ก่อน")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )

        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Depth Range",
                    "Soil",
                    "Behaviour",
                    "gamma",
                    "cu",
                    "qc_f",
                    "qc_eb",
                    "delta_cv",
                    "k0",
                    "flim",
                    "qlim",
                    "Used Parameter",
                    "Unit Shaft",
                    "Qshaft Layer"
                ])
                writer.writerows(results)

            messagebox.showinfo("Success", "Export CSV สำเร็จ")

    root = tk.Tk()
    root.title("Layer-Based CPT Pile Capacity Calculator")
    root.geometry("1550x830")

    tk.Label(
        root,
        text="Layer-Based CPT Pile Capacity Calculator",
        font=("Arial", 18, "bold")
    ).pack(pady=10)

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=15, pady=10)

    left_frame = tk.LabelFrame(main_frame, text="Pile Input", padx=10, pady=10)
    left_frame.pack(side="left", fill="y", padx=10)

    middle_frame = tk.LabelFrame(main_frame, text="Layer Input and Calculation", padx=10, pady=10)
    middle_frame.pack(side="left", fill="both", expand=True, padx=10)

    right_frame = tk.LabelFrame(main_frame, text="Summary Result", padx=10, pady=10)
    right_frame.pack(side="right", fill="y", padx=10)

    tk.Label(left_frame, text="Pile Case").pack(anchor="w")
    pile_case_combo = ttk.Combobox(
        left_frame,
        values=["Custom", "54-in OD", "66-in OD"],
        width=17
    )
    pile_case_combo.pack(pady=5)
    pile_case_combo.current(1)

    tk.Label(left_frame, text="Pile Diameter, D (m)").pack(anchor="w")
    entry_diameter = tk.Entry(left_frame, width=20)
    entry_diameter.pack(pady=4)
    entry_diameter.insert(0, "1.3716")

    tk.Label(left_frame, text="Pile Length, Ltotal (m)").pack(anchor="w")
    entry_length = tk.Entry(left_frame, width=20)
    entry_length.pack(pady=4)
    entry_length.insert(0, "173.563")

    tk.Label(left_frame, text="Analysis Depth, Lembed (m)").pack(anchor="w")
    entry_analysis_depth = tk.Entry(left_frame, width=20)
    entry_analysis_depth.pack(pady=4)
    entry_analysis_depth.insert(0, "157.5")

    tk.Label(left_frame, text="Wall Thickness, WT (m)").pack(anchor="w")
    entry_wt = tk.Entry(left_frame, width=20)
    entry_wt.pack(pady=4)
    entry_wt.insert(0, "0.0445")

    pile_case_combo.bind("<<ComboboxSelected>>", apply_pile_case)

    tk.Label(left_frame, text="Factor of Safety").pack(anchor="w")
    entry_fs = tk.Entry(left_frame, width=20)
    entry_fs.pack(pady=4)
    entry_fs.insert(0, "2.0")

    tk.Label(left_frame, text="CPT-Based Method").pack(anchor="w")
    method_combo = ttk.Combobox(
        left_frame,
        values=["ICP-05", "UWA-05", "Fugro-05", "NGI-05"],
        width=17
    )
    method_combo.pack(pady=5)
    method_combo.current(1)

    tk.Label(left_frame, text="Loading Type").pack(anchor="w")
    loading_combo = ttk.Combobox(
        left_frame,
        values=["Compression", "Tension"],
        width=17
    )
    loading_combo.pack(pady=5)
    loading_combo.current(0)

    tk.Button(left_frame, text="Import CSV", width=24, command=import_csv).pack(pady=6)
    tk.Button(left_frame, text="Calculate", width=24, command=calculate).pack(pady=4)
    tk.Button(left_frame, text="Report qc Profile", width=24, command=show_report_qc_profile).pack(pady=4)
    tk.Button(left_frame, text="Single Method Curve", width=24, command=show_capacity_curve).pack(pady=4)
    tk.Button(left_frame, text="All Methods Compression", width=24, command=lambda: show_all_methods_curve("compression")).pack(pady=4)
    tk.Button(left_frame, text="All Methods Tension", width=24, command=lambda: show_all_methods_curve("tension")).pack(pady=4)
    tk.Button(left_frame, text="Export PDF Report", width=24, command=export_pdf_report).pack(pady=4)
    tk.Button(left_frame, text="Export CSV", width=24, command=export_csv).pack(pady=4)

    tk.Label(
        middle_frame,
        text="Format: from_depth,to_depth,soil_type,behavior,gamma,cu,qc_f(MPa),qc_eb(MPa),delta_cv(deg),k0,flim(kPa),qlim(MPa)"
    ).pack(anchor="w")

    layer_text = tk.Text(middle_frame, height=13, width=120)
    layer_text.pack(fill="x", pady=5)

    layer_text.insert(tk.END, """0,3,clay,cohesive,16.4,1,,,,,,
3,7.9,clay,cohesive,16.4,9,,,,,,
7.9,10.8,clay,cohesive,18.2,16,,,,,,
10.8,14,clay,cohesive,18.4,22,,,,,,
14,20.9,clay,cohesive,17.0,25,,,,,,
20.9,27.4,clay,cohesive,17.7,42,,,,,,
27.4,32.5,clay,cohesive,17.4,55,,,,,,
32.5,36.8,clay,cohesive,17.4,65,,,,,,
36.8,47,clay,cohesive,18.0,65,,,,,,
47,50,clay,cohesive,18.0,85,,,,,,
50,51.6,sand,frictional,18.3,,8,9,28.8,1.0,,
51.6,57.7,sand,frictional,19.2,,27,18,26.1,1.0,,
57.7,61,sand,frictional,19.2,,26,26,26.1,1.0,,
61,64,sand,frictional,18.7,,10.5,10.5,28.8,1.0,,
64,66.7,sand,frictional,18.7,,17,17,28.8,1.0,,
66.7,68.5,sand,frictional,20.0,,26,40,26.1,1.0,,
68.5,71,sand,frictional,20.0,,40,33,26.1,1.0,,
71,74,sand,frictional,20.0,,24,24,26.1,1.0,,
74,77.3,sand,frictional,20.0,,31.5,31.5,26.1,1.0,,
77.3,83,sand,frictional,19.2,,23,25,26.1,1.0,,
83,95.2,sand,frictional,20.1,,30,30,26.1,1.0,,
95.2,102.6,sand,frictional,18.7,,16,16,28.8,1.0,,
102.6,106.8,clay,cohesive,18.9,180,,,,,,
106.8,108.8,sand,frictional,20.0,,20,20,28.8,1.0,,
108.8,110.8,clay,cohesive,20.0,160,,,,,,
110.8,112,sand,frictional,18.1,,18,18,28.8,1.0,,
112,113.7,sand/clay,frictional,18.1,,12,12,28.8,1.0,,2.2
113.7,114.8,clay,cohesive,19.1,230,,,,,,
114.8,115.9,sand,frictional,20.0,,33,33,28.8,1.0,,
115.9,116.9,sand/clay,frictional,19.3,,8,8,28.8,1.0,,2.1
116.9,118.8,sand,frictional,19.1,,17,17,28.8,1.0,,
118.8,123.5,silt,frictional,19.1,,11,11,28.8,1.0,,
123.5,125.5,sand,frictional,19.1,,14.5,14.5,28.8,1.0,,
125.5,129.6,silt/clay,frictional,19.8,,8,8,28.8,1.0,,2.0
129.6,140,clay,cohesive,19.5,250,,,,,,
140,141.7,sand,frictional,19.5,,4.7,4.7,28.8,1.0,,
141.7,150,clay,cohesive,18.5,275,,,,,,
150,152,silt,frictional,20.0,,24,24,28.8,1.0,,
152,157.5,clay,cohesive,18.5,350,,,,,,""")

    columns = (
        "depth_range", "soil", "behavior", "gamma", "cu",
        "qc_f", "qc_eb", "delta", "k0", "flim", "qlim",
        "used", "unit_shaft", "qshaft_layer"
    )

    table = ttk.Treeview(middle_frame, columns=columns, show="headings", height=17)

    headings = {
        "depth_range": "Depth",
        "soil": "Soil",
        "behavior": "Behaviour",
        "gamma": "γ",
        "cu": "cu",
        "qc_f": "qc,f",
        "qc_eb": "qc,eb",
        "delta": "δcv",
        "k0": "K0",
        "flim": "flim",
        "qlim": "qlim",
        "used": "Used",
        "unit_shaft": "Unit Shaft",
        "qshaft_layer": "Qshaft"
    }

    widths = {
        "depth_range": 90,
        "soil": 80,
        "behavior": 80,
        "gamma": 50,
        "cu": 50,
        "qc_f": 50,
        "qc_eb": 50,
        "delta": 50,
        "k0": 45,
        "flim": 55,
        "qlim": 55,
        "used": 60,
        "unit_shaft": 85,
        "qshaft_layer": 90
    }

    for col in columns:
        table.heading(col, text=headings[col])
        table.column(col, width=widths[col], anchor="center")

    table.pack(fill="both", expand=True, pady=10)

    summary_text = tk.StringVar(value="Result will show here")

    tk.Label(
        right_frame,
        textvariable=summary_text,
        font=("Arial", 11),
        justify="left",
        width=38,
        anchor="nw"
    ).pack(pady=10)

    root.mainloop()