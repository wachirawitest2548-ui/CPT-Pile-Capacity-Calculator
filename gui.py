import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from formulas import calculate_capacity, calculate_capacity_curve


def run_app():
    results = []
    graph_depths = []
    graph_qcs = []

    def import_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV file", "*.csv")])
        if not file_path:
            return

        cpt_text.delete("1.0", tk.END)

        with open(file_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                cpt_text.insert(
                    tk.END,
                    f'{row["depth"]},{row["qc"]},{row["soil_type"]}\n'
                )

    def calculate():
        nonlocal results, graph_depths, graph_qcs
        results = []
        graph_depths = []
        graph_qcs = []

        try:
            D = float(entry_diameter.get())
            L = float(entry_length.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            gamma_eff = float(entry_gamma.get())
            tan_delta_cv = float(entry_delta.get())
            method = method_combo.get()

            cpt_lines = cpt_text.get("1.0", tk.END).strip().split("\n")

            rows, summary = calculate_capacity(
                D=D,
                L=L,
                WT=WT,
                FS=FS,
                method=method,
                gamma_eff=gamma_eff,
                tan_delta_cv=tan_delta_cv,
                cpt_lines=cpt_lines
            )

            table.delete(*table.get_children())

            for row in rows:
                values = [
                    row["depth_range"],
                    f'{row["dz"]:.2f}',
                    f'{row["qc"]:.2f}',
                    row["soil_type"],
                    f'{row["unit_shaft"]:.2f}',
                    f'{row["qshaft_layer"]:.2f}'
                ]

                table.insert("", "end", values=values)
                results.append(values)

                graph_depths.append(float(row["depth_range"].split("-")[1]))
                graph_qcs.append(row["qc"])

            summary_text.set(
                f"Method: {method}\n"
                f"Pile Length = {L:.2f} m\n"
                f"Wall Thickness = {WT:.3f} m\n"
                f"γ' = {gamma_eff:.2f} kN/m³\n"
                f"tan(δcv) = {tan_delta_cv:.3f}\n\n"
                f"Ap = {summary['Ap']:.3f} m²\n"
                f"Perimeter = {summary['perimeter']:.3f} m\n"
                f"Ar = {summary['Ar']:.3f}\n"
                f"qc,av,1.5D = {summary['qc_av_1_5D']:.2f} kPa\n"
                f"qbase unit = {summary['q_unit_base']:.2f} kPa\n\n"
                f"Qshaft = {summary['Qshaft']:.2f} kN\n"
                f"Qbase = {summary['Qbase']:.2f} kN\n"
                f"Qult = {summary['Qult']:.2f} kN\n"
                f"Qallow = {summary['Qallow']:.2f} kN"
            )

        except Exception as e:
            messagebox.showerror("Error", f"ข้อมูลผิดหรือกรอกไม่ครบ\n\n{e}")

    def show_cpt_profile():
        if not graph_depths:
            messagebox.showwarning("Warning", "ต้องกด Calculate ก่อน")
            return

        plt.figure(figsize=(7, 6))
        plt.plot(graph_qcs, graph_depths, marker="o", linewidth=2)

        for x, y in zip(graph_qcs, graph_depths):
            plt.annotate(
                f"{x:.0f}",
                (x, y),
                textcoords="offset points",
                xytext=(5, 5)
            )

        plt.gca().invert_yaxis()
        plt.xlabel("qc (kPa)")
        plt.ylabel("Depth (m)")
        plt.title("CPT Cone Resistance Profile")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def show_capacity_curve():
        try:
            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            gamma_eff = float(entry_gamma.get())
            tan_delta_cv = float(entry_delta.get())
            method = method_combo.get()

            cpt_lines = cpt_text.get("1.0", tk.END).strip().split("\n")

            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                gamma_eff=gamma_eff,
                tan_delta_cv=tan_delta_cv,
                cpt_lines=cpt_lines
            )

            if not depths:
                messagebox.showwarning("Warning", "ไม่มีข้อมูลสำหรับสร้าง Capacity Curve")
                return

            plt.figure(figsize=(8, 6))
            plt.plot(qult, depths, "o-", linewidth=2, label="Ultimate Capacity, Qult")
            plt.plot(qallow, depths, "s-", linewidth=2, label="Allowable Capacity, Qallow")

            for x, y in zip(qult, depths):
                plt.annotate(
                    f"{x:.0f}",
                    (x, y),
                    textcoords="offset points",
                    xytext=(5, 5)
                )

            for x, y in zip(qallow, depths):
                plt.annotate(
                    f"{x:.0f}",
                    (x, y),
                    textcoords="offset points",
                    xytext=(5, -15)
                )

            plt.gca().invert_yaxis()
            plt.xlabel("Axial Capacity (kN)")
            plt.ylabel("Pile Penetration Depth (m)")
            plt.title(f"{method} Axial Pile Capacity Curve")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"สร้างกราฟไม่ได้\n\n{e}")

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
                    "dz",
                    "qc",
                    "Soil",
                    "Unit Shaft",
                    "Qshaft Layer"
                ])
                writer.writerows(results)

            messagebox.showinfo("Success", "Export CSV สำเร็จ")

    def export_pdf_report():
        if not graph_depths:
            messagebox.showwarning("Warning", "ต้องกด Calculate ก่อน")
            return

        try:
            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            gamma_eff = float(entry_gamma.get())
            tan_delta_cv = float(entry_delta.get())
            method = method_combo.get()

            cpt_lines = cpt_text.get("1.0", tk.END).strip().split("\n")

            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                gamma_eff=gamma_eff,
                tan_delta_cv=tan_delta_cv,
                cpt_lines=cpt_lines
            )

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")]
            )

            if not file_path:
                return

            with PdfPages(file_path) as pdf:

                # Page 1: Summary
                fig_summary = plt.figure(figsize=(8.27, 11.69))
                plt.axis("off")

                report_text = (
                    "CPT-Based Pile Capacity Calculator\n\n"
                    "Input Parameters\n"
                    "-------------------------\n"
                    f"Method: {method}\n"
                    f"Pile Diameter, D = {entry_diameter.get()} m\n"
                    f"Pile Length, L = {entry_length.get()} m\n"
                    f"Wall Thickness, WT = {entry_wt.get()} m\n"
                    f"Factor of Safety = {entry_fs.get()}\n"
                    f"Effective Unit Weight γ' = {entry_gamma.get()} kN/m³\n"
                    f"tan(δcv) = {entry_delta.get()}\n\n"
                    "Summary Result\n"
                    "-------------------------\n"
                    f"{summary_text.get()}"
                )

                plt.text(0.08, 0.95, report_text, va="top", fontsize=12)
                plt.title("Calculation Summary", fontsize=16, fontweight="bold")
                pdf.savefig(fig_summary)
                plt.close(fig_summary)

                # Page 2: CPT Profile
                fig_cpt = plt.figure(figsize=(8.27, 11.69))
                plt.plot(graph_qcs, graph_depths, "o-", linewidth=2)

                for x, y in zip(graph_qcs, graph_depths):
                    plt.annotate(
                        f"{x:.0f}",
                        (x, y),
                        textcoords="offset points",
                        xytext=(5, 5)
                    )

                plt.gca().invert_yaxis()
                plt.xlabel("qc (kPa)")
                plt.ylabel("Depth (m)")
                plt.title("CPT Cone Resistance Profile")
                plt.grid(True)
                plt.tight_layout()
                pdf.savefig(fig_cpt)
                plt.close(fig_cpt)

                # Page 3: Capacity Curve
                fig_capacity = plt.figure(figsize=(8.27, 11.69))
                plt.plot(qult, depths, "o-", linewidth=2, label="Ultimate Capacity, Qult")
                plt.plot(qallow, depths, "s-", linewidth=2, label="Allowable Capacity, Qallow")

                for x, y in zip(qult, depths):
                    plt.annotate(
                        f"{x:.0f}",
                        (x, y),
                        textcoords="offset points",
                        xytext=(5, 5)
                    )

                for x, y in zip(qallow, depths):
                    plt.annotate(
                        f"{x:.0f}",
                        (x, y),
                        textcoords="offset points",
                        xytext=(5, -15)
                    )

                plt.gca().invert_yaxis()
                plt.xlabel("Axial Capacity (kN)")
                plt.ylabel("Pile Penetration Depth (m)")
                plt.title(f"{method} Axial Pile Capacity Curve")
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                pdf.savefig(fig_capacity)
                plt.close(fig_capacity)

            messagebox.showinfo("Success", "Export PDF Report สำเร็จ")

        except Exception as e:
            messagebox.showerror("Error", f"Export PDF ไม่ได้\n\n{e}")

    root = tk.Tk()
    root.title("CPT-Based Pile Capacity Calculator")
    root.geometry("1300x780")

    tk.Label(
        root,
        text="CPT-Based Pile Capacity Calculator",
        font=("Arial", 18, "bold")
    ).pack(pady=10)

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=15, pady=10)

    left_frame = tk.LabelFrame(main_frame, text="Input", padx=10, pady=10)
    left_frame.pack(side="left", fill="y", padx=10)

    middle_frame = tk.LabelFrame(
        main_frame,
        text="CPT Data and Layer Calculation",
        padx=10,
        pady=10
    )
    middle_frame.pack(side="left", fill="both", expand=True, padx=10)

    right_frame = tk.LabelFrame(main_frame, text="Summary Result", padx=10, pady=10)
    right_frame.pack(side="right", fill="y", padx=10)

    tk.Label(left_frame, text="Pile Diameter, D (m)").pack(anchor="w")
    entry_diameter = tk.Entry(left_frame, width=20)
    entry_diameter.pack(pady=4)
    entry_diameter.insert(0, "1.2")

    tk.Label(left_frame, text="Pile Length, L (m)").pack(anchor="w")
    entry_length = tk.Entry(left_frame, width=20)
    entry_length.pack(pady=4)
    entry_length.insert(0, "5")

    tk.Label(left_frame, text="Wall Thickness, WT (m)").pack(anchor="w")
    entry_wt = tk.Entry(left_frame, width=20)
    entry_wt.pack(pady=4)
    entry_wt.insert(0, "0.025")

    tk.Label(left_frame, text="Factor of Safety").pack(anchor="w")
    entry_fs = tk.Entry(left_frame, width=20)
    entry_fs.pack(pady=4)
    entry_fs.insert(0, "2.5")

    tk.Label(left_frame, text="Effective Unit Weight γ' (kN/m³)").pack(anchor="w")
    entry_gamma = tk.Entry(left_frame, width=20)
    entry_gamma.pack(pady=4)
    entry_gamma.insert(0, "10")

    tk.Label(left_frame, text="tan(δcv)").pack(anchor="w")
    entry_delta = tk.Entry(left_frame, width=20)
    entry_delta.pack(pady=4)
    entry_delta.insert(0, "0.55")

    tk.Label(left_frame, text="CPT-Based Method").pack(anchor="w")
    method_combo = ttk.Combobox(
        left_frame,
        values=["ICP-05", "UWA-05", "Fugro-05", "NGI-05"],
        width=17
    )
    method_combo.pack(pady=5)
    method_combo.current(0)

    tk.Button(left_frame, text="Import CSV", width=18, command=import_csv).pack(pady=6)
    tk.Button(left_frame, text="Calculate", width=18, command=calculate).pack(pady=4)
    tk.Button(left_frame, text="CPT Profile", width=18, command=show_cpt_profile).pack(pady=4)
    tk.Button(left_frame, text="Capacity Curve", width=18, command=show_capacity_curve).pack(pady=4)
    tk.Button(left_frame, text="Export CSV", width=18, command=export_csv).pack(pady=4)
    tk.Button(left_frame, text="Export PDF Report", width=18, command=export_pdf_report).pack(pady=4)

    tk.Label(middle_frame, text="Format: depth,qc,soil_type").pack(anchor="w")

    cpt_text = tk.Text(middle_frame, height=8, width=75)
    cpt_text.pack(fill="x", pady=5)

    cpt_text.insert(tk.END, """1,3000,clay
2,3500,clay
3,4200,sand
4,5000,sand
5,6000,sand""")

    columns = ("depth_range", "dz", "qc", "soil", "unit_shaft", "qshaft_layer")
    table = ttk.Treeview(middle_frame, columns=columns, show="headings", height=17)

    headings = {
        "depth_range": "Depth Range (m)",
        "dz": "dz (m)",
        "qc": "qc (kPa)",
        "soil": "Soil",
        "unit_shaft": "Unit Shaft (kPa)",
        "qshaft_layer": "Qshaft Layer (kN)"
    }

    widths = {
        "depth_range": 120,
        "dz": 70,
        "qc": 90,
        "soil": 80,
        "unit_shaft": 130,
        "qshaft_layer": 150
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
        width=34,
        anchor="nw"
    ).pack(pady=10)

    root.mainloop()