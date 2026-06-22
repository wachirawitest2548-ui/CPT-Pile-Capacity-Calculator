import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import math
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

# =========================
# REPORT FONT SETTINGS
# Pick an installed font only, so matplotlib will not spam findfont warnings.
# On Windows this usually selects Arial / Segoe UI / Calibri.
# =========================
from matplotlib import font_manager

def _pick_report_font():
    preferred = ["Arial Narrow", "Arial", "Segoe UI", "Calibri", "Tahoma", "DejaVu Sans"]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in installed:
            return name
    return "DejaVu Sans"

REPORT_FONT = _pick_report_font()
REPORT_FONT_FAMILY = [REPORT_FONT]

plt.rcParams.update({
    "font.family": REPORT_FONT,
    "font.sans-serif": REPORT_FONT_FAMILY,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})

# =========================
# PTTEP ACCESS CONTROL
# This is a lightweight local verification layer for demo/internal-use feel.
# It is NOT a replacement for real enterprise authentication.
# =========================
AUTHORIZED_EMAIL_DOMAIN = "@pttep.com"
LICENSE_KEY = "PTTEP-2026-CPT-AXIAL"
APP_VERSION = "1.0"
IS_DEMO_MODE = False

def set_table_font(table, body_size=7.0, header_size=7.2):
    for (r, c), cell in table.get_celld().items():
        txt = cell.get_text()
        txt.set_fontfamily(REPORT_FONT)
        if r == 0:
            txt.set_fontsize(header_size)
            txt.set_fontweight("bold")
        else:
            txt.set_fontsize(body_size)
            txt.set_fontweight("normal")


from layer_formulas import (
    calculate_layer_capacity,
    calculate_capacity_curve,
    parse_layer_lines,
    layer_value
)



def show_pttep_login():
    """
    Modern PTTEP-style access screen.
    Requirements:
    - Email must end with @pttep.com
    - License key must match LICENSE_KEY

    This is a lightweight local verification layer for demo/internal-use feel.
    It is not a replacement for real enterprise authentication.
    """
    login_ok = {"value": False}

    login = tk.Tk()
    login.title("PTTEP User Verification")
    login.geometry("560x610")
    login.resizable(False, False)
    login.configure(bg="#F4F7FB")

    # Center window
    login.update_idletasks()
    w = 560
    h = 610
    x = (login.winfo_screenwidth() // 2) - (w // 2)
    y = (login.winfo_screenheight() // 2) - (h // 2)
    login.geometry(f"{w}x{h}+{x}+{y}")

    # =========================
    # LOGIN THEME
    # =========================
    style = ttk.Style(login)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "LoginPrimary.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(10, 8),
        background="#003B71",
        foreground="white",
        bordercolor="#003B71",
        relief="flat"
    )
    style.map(
        "LoginPrimary.TButton",
        background=[("active", "#0056A6"), ("pressed", "#002A52")],
        foreground=[("active", "white")]
    )

    style.configure(
        "LoginSecondary.TButton",
        font=("Segoe UI", 10),
        padding=(16, 10),
        background="#FFFFFF",
        foreground="#003B71",
        bordercolor="#D8E1EC",
        relief="flat"
    )
    style.map(
        "LoginSecondary.TButton",
        background=[("active", "#EAF2FF"), ("pressed", "#D8E8FF")]
    )

    # =========================
    # TOP BRAND PANEL
    # =========================
    top = tk.Frame(login, bg="#003B71", height=190)
    top.pack(fill="x", side="top")
    top.pack_propagate(False)

    logo_holder = tk.Frame(top, bg="#003B71", width=105, height=105)
    logo_holder.pack(pady=(24, 8))
    logo_holder.pack_propagate(False)

    try:
        from PIL import Image, ImageTk

        base_dir = Path(__file__).resolve().parent
        logo_path = base_dir / "PTTEP_Logo.svg.png"
        if not logo_path.exists():
            alt_logo_path = base_dir / "PTTEP_Logo.svg(1).png"
            if alt_logo_path.exists():
                logo_path = alt_logo_path

        logo_img = Image.open(logo_path).convert("RGBA")

        # Crop out only the lower PTTEP wordmark, while keeping the full droplet shape.
        # thumbnail() preserves aspect ratio so the droplet will not look thin/stretched.
        w, h = logo_img.size
        logo_img = logo_img.crop((
            int(w * 0.18),  # left
            0,              # top
            int(w * 0.82),  # right
            int(h * 0.72)   # bottom: removes PTTEP wordmark but keeps full droplet
        ))
        logo_img.thumbnail((92, 92), Image.LANCZOS)

        login_logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(
            logo_holder,
            image=login_logo,
            bg="#003B71",
            bd=0,
            highlightthickness=0
        )
        logo_label.image = login_logo
        logo_label.pack(expand=True)

    except Exception as e:
        print("Login logo load error:", e)
        tk.Label(
            logo_holder,
            text="PTTEP",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#003B71"
        ).pack(expand=True)

    tk.Label(
        top,
        text="PTTEP CPT-Based Axial Pile Capacity Calculator",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="#003B71"
    ).pack()

    tk.Label(
        top,
        text=f"Version {APP_VERSION}  •  Authorized Internal Use Only  •  DEMO AVAILABLE",
        font=("Segoe UI", 9),
        fg="#C7D9F2",
        bg="#003B71"
    ).pack(pady=(5, 0))

    # =========================
    # LOGIN CARD
    # =========================
    card_shadow = tk.Frame(login, bg="#D8E1EC")
    card_shadow.pack(fill="x", padx=44, pady=(26, 0))

    card = tk.Frame(card_shadow, bg="white", padx=28, pady=24)
    card.pack(fill="both", expand=True, padx=1, pady=1)

    tk.Label(
        card,
        text="User Verification",
        font=("Segoe UI", 16, "bold"),
        fg="#003B71",
        bg="white"
    ).pack(anchor="w")

    tk.Label(
        card,
        text="Please verify your PTTEP access before continuing.",
        font=("Segoe UI", 9),
        fg="#64748B",
        bg="white"
    ).pack(anchor="w", pady=(4, 18))

    tk.Label(
        card,
        text="PTTEP Email",
        font=("Segoe UI", 9, "bold"),
        fg="#334155",
        bg="white"
    ).pack(anchor="w")

    email_entry = tk.Entry(
        card,
        width=42,
        font=("Segoe UI", 10),
        bg="#F8FBFF",
        fg="#0B1F3A",
        relief="solid",
        bd=1,
        insertbackground="#003B71"
    )
    email_entry.pack(fill="x", pady=(5, 14), ipady=7)

    tk.Label(
        card,
        text="License Key",
        font=("Segoe UI", 9, "bold"),
        fg="#334155",
        bg="white"
    ).pack(anchor="w")

    key_entry = tk.Entry(
        card,
        width=42,
        show="*",
        font=("Segoe UI", 10),
        bg="#F8FBFF",
        fg="#0B1F3A",
        relief="solid",
        bd=1,
        insertbackground="#003B71"
    )
    key_entry.pack(fill="x", pady=(5, 10), ipady=7)

    status_label = tk.Label(
        card,
        text="",
        fg="#B42318",
        bg="white",
        font=("Segoe UI", 8)
    )
    status_label.pack(anchor="w", pady=(0, 10))

    def demo():
        global IS_DEMO_MODE
        IS_DEMO_MODE = True
        login_ok["value"] = True
        login.destroy()

    def verify():
        email = email_entry.get().strip().lower()
        key = key_entry.get().strip()

        if not email:
            status_label.config(text="Please enter PTTEP email.")
            return

        if not email.endswith(AUTHORIZED_EMAIL_DOMAIN):
            status_label.config(text=f"Access denied: email must end with {AUTHORIZED_EMAIL_DOMAIN}")
            return

        if key != LICENSE_KEY:
            status_label.config(text="Access denied: invalid license key.")
            return

        login_ok["value"] = True
        login.destroy()

    def cancel():
        login_ok["value"] = False
        login.destroy()

    btn_frame = tk.Frame(card, bg="white")
    btn_frame.pack(fill="x", pady=(5, 0))

    continue_btn = ttk.Button(
        btn_frame,
        text="Verify and Continue",
        command=verify,
        style="LoginPrimary.TButton"
    )
    continue_btn.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 6)
    )

    demo_btn = ttk.Button(
        btn_frame,
        text="Demo Mode",
        command=demo,
        style="LoginSecondary.TButton"
    )
    demo_btn.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 6)
    )

    exit_btn = ttk.Button(
        btn_frame,
        text="Exit",
        command=cancel,
        style="LoginSecondary.TButton"
    )
    exit_btn.pack(
        side="left",
        fill="x",
        expand=True
    )

    tk.Label(
        card,
        text="Demo Mode allows calculation and graph generation only.\nExport features are disabled.",
        font=("Segoe UI", 8),
        fg="#64748B",
        bg="white",
        justify="center",
        wraplength=650
    ).pack(pady=(10, 0))

    # Footer text
    tk.Label(
        login,
        text="For authorized PTTEP internal engineering use only.",
        font=("Segoe UI", 8),
        fg="#64748B",
        bg="#F4F7FB"
    ).pack(pady=(18, 0))

    email_entry.focus_set()
    login.bind("<Return>", lambda event: verify())
    login.protocol("WM_DELETE_WINDOW", cancel)
    login.mainloop()

    return login_ok["value"]


def run_app():
    # PTTEP verification screen before launching the main calculator GUI.
    if not show_pttep_login():
        return

    results = []
    summary_vars = {}

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
                    f'{row["gamma_top"]},{row["gamma_bot"]},{row["cu_top"]},{row["cu_bot"]},'
                    f'{row["qc_f"]},{row["qc_eb"]},'
                    f'{row["delta_cv"]},{row["k0"]},{row["flim"]},{row["qlim"]}\n'
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

            # Per-row breakdown for engineering discussion:
            # Layer Qshaft = shaft contribution of that layer only
            # Cum. Qshaft = accumulated shaft resistance down to that depth
            # Qbase = end bearing at that depth
            # Qult = Cum. Qshaft + Qbase
            tip_summary_cache = {}

            def get_tip_summary_at_depth(depth):
                depth = min(float(depth), analysis_depth)
                depth_key = round(depth, 6)
                if depth_key not in tip_summary_cache:
                    _, tip_summary, _ = calculate_layer_capacity(
                        D=D,
                        L=depth_key,
                        WT=WT,
                        FS=FS,
                        method=method,
                        layer_lines=layer_lines,
                        loading_type=loading_type
                    )
                    tip_summary_cache[depth_key] = tip_summary
                return tip_summary_cache[depth_key]

            for row in rows:
                try:
                    row_to_depth = float(str(row["depth_range"]).split("-")[-1])
                    tip_summary = get_tip_summary_at_depth(row_to_depth)
                    cum_qshaft = tip_summary["Qshaft"]
                    qbase_at_depth = tip_summary["Qbase"]
                    qult_at_depth = tip_summary["Qult"]
                except Exception:
                    cum_qshaft = None
                    qbase_at_depth = None
                    qult_at_depth = None

                values = [
                    row["depth_range"],
                    row["soil_type"],
                    row["behavior"],
                    f'{row["gamma"]:.1f}',
                    "-" if row.get("gamma_eff") is None else f'{row["gamma_eff"]:.2f}',
                    "-" if row.get("p0_layer") is None else f'{row["p0_layer"]:.2f}',
                    "-" if row.get("cum_p0") is None else f'{row["cum_p0"]:.2f}',
                    "-" if row["cu"] is None else f'{row["cu"]:.1f}',
                    "-" if row["qc_f_mpa"] is None else f'{row["qc_f_mpa"]:.1f}',
                    "-" if row["qc_eb_mpa"] is None else f'{row["qc_eb_mpa"]:.1f}',
                    "-" if row["delta_cv"] is None else f'{row["delta_cv"]:.1f}',
                    "-" if row["k0"] is None else f'{row["k0"]:.2f}',
                    "-" if row["flim"] is None else f'{row["flim"]:.1f}',
                    "-" if row["qlim_mpa"] is None else f'{row["qlim_mpa"]:.1f}',
                    row["used_parameter"],
                    f'{row["unit_shaft"]:.2f}',
                    f'{row["qshaft_layer"]:.2f}',
                    "-" if cum_qshaft is None else f'{cum_qshaft:.2f}',
                    "-" if qbase_at_depth is None else f'{qbase_at_depth:.2f}',
                    "-" if qult_at_depth is None else f'{qult_at_depth:.2f}'
                ]

                table.insert("", "end", values=values)
                results.append(values)

            qc_eb_text = "Not used / no qc_eb at pile tip"
            if summary["qc_eb_av_1_5D"] is not None:
                qc_eb_text = f'{summary["qc_eb_av_1_5D"] / 1000:.2f} MPa'

            update_summary_panel(
                D=D,
                pile_length=pile_length,
                analysis_depth=analysis_depth,
                WT=WT,
                FS=FS,
                method=method,
                loading_type=summary["loading_type"].capitalize(),
                summary=summary,
                qc_eb_text=qc_eb_text
            )

        except Exception as e:
            messagebox.showerror("Error", f"ข้อมูลผิดหรือกรอกไม่ครบ\n\n{e}")

    def update_summary_panel(D, pile_length, analysis_depth, WT, FS, method, loading_type, summary, qc_eb_text):
        """
        Update modern summary cards on the right panel.
        Values are shown as engineering dashboard cards instead of one long text block.
        """
        def setv(key, value):
            if key in summary_vars:
                summary_vars[key].set(value)

        setv("pile_case", pile_case_combo.get())
        setv("method", method)
        setv("loading", loading_type)

        setv("D", f"{D:.4f} m")
        setv("pile_length", f"{pile_length:.3f} m")
        setv("analysis_depth", f"{analysis_depth:.3f} m")
        setv("WT", f"{WT:.4f} m")
        setv("FS", f"{FS:.2f}")

        setv("base_model", summary["base_model"])
        setv("Ap", f"{summary['Ap']:.3f} m²")
        setv("perimeter", f"{summary['perimeter']:.3f} m")
        setv("Ar", f"{summary['Ar']:.3f}")
        setv("qc_eb", qc_eb_text)
        setv("qbase_unit", f"{summary['q_unit_base']:.2f} kPa")

        setv("Qshaft", f"{summary['Qshaft'] / 1000:.2f} MN")
        setv("Qbase", f"{summary['Qbase'] / 1000:.2f} MN")
        setv("Qult", f"{summary['Qult'] / 1000:.2f} MN")
        setv("Qallow", f"{summary['Qallow'] / 1000:.2f} MN")

    def plot_qc_profile_to_current_fig(layers):
        """
        Fugro-style qc profile page.
        - A4 portrait fixed size
        - qc is plotted as step profile
        - cohesive/clay layers are blank in qc plots
        - no bbox_inches='tight' is used when saving, so PDF remains A4
        """

        def build_step_profile(layers, key):
            """
            Build a Fugro-style step profile using TOP and BOTTOM qc values.
            Important: do not use layer.get("qc_f") / layer.get("qc_eb") only,
            because some parsed layer dictionaries only store qc_f_top/qc_f_bot
            and qc_eb_top/qc_eb_bot. This version plots every frictional layer
            down to the deepest input depth, including long 400–500 m examples.
            """
            xs = []
            ys = []
            last_q_bot = None
            last_z_bot = None

            for layer in layers:
                z1 = layer["from_depth"]
                z2 = layer["to_depth"]

                # Fugro plate leaves clay/cohesive zones blank in qc plots.
                if layer["behavior"] == "cohesive":
                    xs.append(None)
                    ys.append(None)
                    last_q_bot = None
                    last_z_bot = None
                    continue

                q_top = layer_value(layer, key, z1)
                q_bot = layer_value(layer, key, z2)

                if q_top is None or q_bot is None:
                    xs.append(None)
                    ys.append(None)
                    last_q_bot = None
                    last_z_bot = None
                    continue

                q_top = q_top / 1000.0  # kPa -> MPa
                q_bot = q_bot / 1000.0  # kPa -> MPa

                # Horizontal connector between consecutive frictional layers.
                if last_q_bot is not None and last_z_bot is not None and abs(last_z_bot - z1) < 1e-6:
                    xs.extend([last_q_bot, q_top])
                    ys.extend([z1, z1])

                # Vertical/stepped profile in current layer.
                xs.extend([q_top, q_bot])
                ys.extend([z1, z2])

                last_q_bot = q_bot
                last_z_bot = z2

            return xs, ys

        def draw_soil_column(ax_soil, layers, max_depth):
            ax_soil.set_xlim(0, 1)
            ax_soil.set_ylim(max_depth, 0)
            ax_soil.set_xticks([])
            ax_soil.tick_params(left=False, labelleft=False)
            ax_soil.grid(True, axis="y", linestyle="-", linewidth=0.45, color="black")

            for layer in layers:
                z1 = layer["from_depth"]
                z2 = layer["to_depth"]
                if z2 <= z1:
                    continue

                z_mid = 0.5 * (z1 + z2)
                soil = layer["soil_type"].title()
                behavior = layer["behavior"]

                if behavior == "cohesive":
                    hatch = ""
                    code = "C"
                elif behavior == "frictional":
                    hatch = "///"
                    code = "F"
                else:
                    hatch = "..."
                    code = "R"

                ax_soil.fill_betweenx(
                    [z1, z2],
                    0.00,
                    0.42,
                    facecolor="white",
                    edgecolor="black",
                    hatch=hatch,
                    linewidth=0.55
                )

                ax_soil.text(0.21, z_mid, code, ha="center", va="center", fontsize=5.7, fontweight="bold")
                ax_soil.text(0.72, z_mid, soil, ha="center", va="center", fontsize=4.7)

            ax_soil.set_title("Ground\nBehaviour\n/\nGround\nUnit\nName", fontsize=6.2, pad=8)
            for spine in ax_soil.spines.values():
                spine.set_linewidth(0.8)

        plt.rcParams["font.family"] = REPORT_FONT
        plt.rcParams["font.sans-serif"] = REPORT_FONT_FAMILY
        plt.rcParams["axes.linewidth"] = 0.8

        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        # Dynamic depth limit for long example profiles.
        max_depth = max(layer["to_depth"] for layer in layers)
        max_depth = int(math.ceil(max_depth / 20.0) * 20)

        # Fugro-like page layout: plot area smaller, with larger margins.
        ax_f = fig.add_axes([0.14, 0.20, 0.25, 0.63])
        ax_eb = fig.add_axes([0.42, 0.20, 0.25, 0.63], sharey=ax_f)
        ax_soil = fig.add_axes([0.72, 0.20, 0.13, 0.63], sharey=ax_f)

        qc_f_x, qc_f_y = build_step_profile(layers, "qc_f")
        qc_eb_x, qc_eb_y = build_step_profile(layers, "qc_eb")

        ax_f.plot(qc_f_x, qc_f_y, color="black", linewidth=1.05)
        ax_eb.plot(qc_eb_x, qc_eb_y, color="black", linewidth=1.05)

        # Dynamic qc x-axis. Normal reports remain 0–60 MPa;
        # high-qc stress-test examples can expand to 100–150 MPa.
        qc_values = []
        for layer in layers:
            if layer["behavior"] != "cohesive":
                for key_name in ["qc_f", "qc_eb"]:
                    q1 = layer_value(layer, key_name, layer["from_depth"])
                    q2 = layer_value(layer, key_name, layer["to_depth"])
                    if q1 is not None:
                        qc_values.append(q1 / 1000.0)
                    if q2 is not None:
                        qc_values.append(q2 / 1000.0)

        qc_xmax = 60
        qc_tick_step = 20
        if qc_values and max(qc_values) > 60:
            qc_xmax = int(math.ceil(max(qc_values) / 20.0) * 20)
            qc_tick_step = 20

        for ax in [ax_f, ax_eb]:
            ax.set_xlim(0, qc_xmax)
            ax.set_ylim(max_depth, 0)
            ax.set_xticks(range(0, int(qc_xmax) + 1, qc_tick_step))
            ax.set_yticks(range(0, int(max_depth) + 1, 20))
            ax.grid(True, which="major", linestyle="-", linewidth=0.55, color="black")
            ax.tick_params(axis="both", labelsize=6.5)
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()
            for spine in ax.spines.values():
                spine.set_linewidth(0.8)

        ax_f.set_title("Cone Resistance Used for Skin Friction [MPa]", fontsize=6.6, pad=8)
        ax_eb.set_title("Cone Resistance Used for End Bearing [MPa]", fontsize=6.6, pad=8)
        ax_f.set_ylabel("Depth Below Seafloor [m]", fontsize=7)
        plt.setp(ax_eb.get_yticklabels(), visible=False)

        draw_soil_column(ax_soil, layers, max_depth)

        # Footer / title block similar to Fugro plate.
        fig.text(
            0.50,
            0.085,
            "CONE RESISTANCE PROFILE FOR UNIT SKIN FRICTION AND UNIT END BEARING COMPUTATION",
            ha="center",
            fontsize=8.3,
            fontweight="bold"
        )
        fig.text(0.50, 0.065, "DRIVEN OPEN-ENDED CIRCULAR PILE", ha="center", fontsize=6.5)

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
        analysis_depth = float(entry_analysis_depth.get())
        layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
        layers = parse_layer_lines(layer_lines)

        # Dynamic depth limit for long example profiles.
        max_depth = max(layer["to_depth"] for layer in layers)
        max_depth = int(math.ceil(max_depth / 20.0) * 20)

        plt.rcParams["font.family"] = REPORT_FONT
        plt.rcParams["font.sans-serif"] = REPORT_FONT_FAMILY
        plt.rcParams["axes.linewidth"] = 0.8

        methods = [
            ("API Main Text", "API RP 2GEO (2011) - Main Text Method", "orange", "-"),
            ("ICP-05", "API RP 2GEO (2011) - Method 1, Simplified ICP-05", "green", "--"),
            ("UWA-05", "API RP 2GEO (2011) - Method 2, Offshore UWA-05", "magenta", "-"),
            ("Fugro-05", "API RP 2GEO (2011) - Method 3, Fugro-05", "cyan", "-."),
            ("NGI-05", "API RP 2GEO (2011) - Method 4, NGI-05", "red", "--")
        ]

        def draw_soil_column(ax_soil, layers, max_depth):
            ax_soil.set_xlim(0, 1)
            ax_soil.set_ylim(max_depth, 0)
            ax_soil.set_xticks([])
            ax_soil.tick_params(left=False, labelleft=False)
            ax_soil.grid(True, axis="y", color="black", linewidth=0.35, alpha=0.7)

            for layer in layers:
                z1 = layer["from_depth"]
                z2 = min(layer["to_depth"], analysis_depth)
                if z2 <= z1:
                    continue

                soil = layer["soil_type"].title()
                behavior = layer["behavior"]
                if behavior == "cohesive":
                    hatch = ""
                    code = "C"
                elif behavior == "frictional":
                    hatch = "///"
                    code = "F"
                else:
                    hatch = "..."
                    code = "R"

                ax_soil.fill_betweenx(
                    [z1, z2],
                    0.00,
                    0.42,
                    facecolor="white",
                    edgecolor="black",
                    hatch=hatch,
                    linewidth=0.55
                )

                mid = 0.5 * (z1 + z2)
                thickness = z2 - z1

                # Larger fonts for readability, but hide soil-name text in very thin layers
                # to avoid overlap. The behaviour code (C/F) is still shown.
                if thickness < 1.5:
                    code_fontsize = 4.8
                    soil_fontsize = None
                elif thickness < 3.0:
                    code_fontsize = 5.4
                    soil_fontsize = 4.5
                else:
                    code_fontsize = 6.2
                    soil_fontsize = 5.4 if len(soil) <= 8 else 4.8

                ax_soil.text(0.21, mid, code, ha="center", va="center", fontsize=code_fontsize, fontweight="bold")

                if soil_fontsize is not None:
                    ax_soil.text(0.72, mid, soil, ha="center", va="center", fontsize=soil_fontsize)

            ax_soil.set_title("Ground\nBehaviour\n/\nGround\nUnit\nName", fontsize=6.0, pad=8)
            for spine in ax_soil.spines.values():
                spine.set_linewidth(0.8)

        title_word = "COMPRESSION" if loading_type == "compression" else "TENSION"
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")

        # Fugro-like A4 layout with cleaner bottom information area.
        # More space is reserved below the plot for legend, notes, title and footer.
        ax = fig.add_axes([0.11, 0.27, 0.63, 0.58])
        ax_soil = fig.add_axes([0.78, 0.27, 0.14, 0.58], sharey=ax)

        all_capacity_values = []

        for method, label, color, linestyle in methods:
            depths, qult, _ = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type
            )

            plot_depths = []
            plot_qult = []
            for d, q in zip(depths, qult):
                if d <= analysis_depth:
                    plot_depths.append(d)
                    plot_qult.append(q)
                    all_capacity_values.append(q)

            if plot_depths:
                ax.plot(
                    plot_qult,
                    plot_depths,
                    color=color,
                    linestyle=linestyle,
                    linewidth=1.05,
                    label=label
                )

        # Dynamic x-axis limit for long / high-capacity example cases.
        # Normal reports stay close to 0–120 MN, but deep test cases can exceed 300–500 MN.
        if all_capacity_values:
            x_max = max(all_capacity_values)
            if x_max <= 120:
                x_max = 120
                x_tick_step = 10
            else:
                x_max = int(math.ceil(x_max / 50.0) * 50)
                x_tick_step = 50
        else:
            x_max = 120
            x_tick_step = 10

        ax.set_xlim(0, x_max)
        ax.set_ylim(max_depth, 0)
        ax.set_xticks(range(0, int(x_max) + 1, x_tick_step))
        ax.set_yticks(range(0, int(max_depth) + 1, 20))
        ax.set_yticks(range(0, int(max_depth) + 1, 10), minor=True)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xlabel(f"Ultimate Axial Pile Capacity in {title_word.title()} [MN]", fontsize=7)
        ax.set_ylabel("Depth Below Seafloor [m]", fontsize=7)
        ax.tick_params(axis="both", labelsize=6.5)
        ax.grid(True, which="major", color="black", linewidth=0.50)
        ax.grid(True, which="minor", color="black", linewidth=0.22, alpha=0.45)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

        draw_soil_column(ax_soil, layers, max_depth)

        # Header block.
        fig.text(0.50, 0.940, f"ULTIMATE AXIAL PILE CAPACITY IN {title_word}", ha="center", fontsize=8.2, fontweight="bold")
        fig.text(0.50, 0.920, f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}", ha="center", fontsize=6.2)
        fig.text(0.82, 0.963, "PTTEP International Limited", ha="center", fontsize=5.6)

        # =========================
        # CLEAN BOTTOM INFORMATION AREA
        # Legend, notes, title and footer are figure-level blocks.
        # This avoids overlap with axes and keeps the report readable.
        # =========================
        handles, labels = ax.get_legend_handles_labels()

        fig.legend(
            handles,
            labels,
            loc="lower left",
            bbox_to_anchor=(0.10, 0.185),
            fontsize=7.0,
            frameon=False,
            ncol=1,
            handlelength=3.2,
            handletextpad=0.8,
            labelspacing=0.30,
            borderaxespad=0.0
        )

        notes_text = (
            "Notes:\n"
            "1. API Main Text Method: Clay f = αsu, q = 9su; Sand f = βp'0, q = Nq p'0,tip.\n"
            "2. CPT-Based Methods: ICP-05, UWA-05, Fugro-05 and NGI-05 are in accordance with API RP 2GEO (2011); "
            "NGI-05 applies the 0.1p'0 lower bound.\n"
            "3. For API Main Text sand layers, Dr is estimated using a WPA-01/Fugro-calibrated CPT trend only for automatic β/Nq selection; "
            "Table 1 flim and qlim are applied."
        )

        fig.text(
            0.10,
            0.150,
            notes_text,
            fontsize=6.5,
            ha="left",
            va="top",
            linespacing=1.22
        )

        # Bottom title block
        fig.text(
            0.50,
            0.085,
            f"ULTIMATE AXIAL PILE CAPACITY IN {title_word}",
            ha="center",
            fontsize=8.2,
            fontweight="bold"
        )
        fig.text(
            0.50,
            0.067,
            f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}",
            ha="center",
            fontsize=6.5
        )

        # Report footer and plate number
        fig.text(
            0.10,
            0.038,
            "F136127MGT-ENG-RPT-003 02 | Piled Foundation Analyses Report for WPA-01 Platform Site",
            ha="left",
            fontsize=5.8
        )

        plate_no = "Plate 3.xx"
        if pile_case_combo.get() == "54-in OD" and loading_type == "compression":
            plate_no = "Plate 3.13"
        elif pile_case_combo.get() == "66-in OD" and loading_type == "compression":
            plate_no = "Plate 3.15"
        elif loading_type == "tension":
            plate_no = "Plate 3.17"
        fig.text(0.10, 0.026, plate_no, ha="left", fontsize=5.8)

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


    def make_input_parameter_table_fig(layers_subset, page_no=1):
        """
        PTTEP/Fugro-style input parameter table page.
        Landscape A4, fixed layout.
        Table size is reduced and cells are balanced to look closer to the reference report.
        """
        fig = plt.figure(figsize=(11.69, 8.27), dpi=150, facecolor="white")

        # =========================
        # TOP RUNNING TEXT
        # =========================
        fig.text(
            0.115,
            0.952,
            "GeODin layout: 0-Parameters (all cpt methods modified).GLO (API main text CPT methods) - printed: 2022-Mar-16 13:57\n"
            "GERRIT run: WPA-01 54-in Pile Cap API(2011)(f\\Model=api(11)\\CPT\\zFricModel=api(11)) | WPA-01 Axial Pile Cap | 54-in Driven open-ended circular pile",
            fontsize=5.2,
            ha="left",
            va="top",
            color="#6f6f6f",
        )

        fig.text(
            0.665,
            0.952,
            "Execution: t-z and q-z data assessment (APICAP v2.1.7) 2022-Mar-16 11:36",
            fontsize=5.2,
            ha="left",
            va="top",
            color="#6f6f6f",
        )

        # =========================
        # PTTEP LOGO
        # Put PTTEP_Logo.svg.png in the same folder as layer_gui.py / main.py.
        # =========================
        try:
            base_dir = Path(__file__).resolve().parent
            logo_path = base_dir / "PTTEP_Logo.svg.png"
            logo_img = mpimg.imread(str(logo_path))

            # Reduced size and moved slightly upward/right to create more breathing room.
            logo_ax = fig.add_axes([0.868, 0.822, 0.070, 0.088])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")

            fig.text(
                0.903,
                0.785,
                "PTTEP International Limited",
                fontsize=6.2,
                color="black",
                ha="center",
                va="top",
            )
        except Exception:
            fig.text(
                0.903,
                0.852,
                "PTTEP",
                fontsize=15,
                fontweight="bold",
                color="#003b71",
                ha="center",
                va="center",
            )
            fig.text(
                0.903,
                0.826,
                "PTTEP International Limited",
                fontsize=6.2,
                color="black",
                ha="center",
                va="center",
            )

        # =========================
        # LEFT SIDE VERTICAL TEXT
        # =========================
        fig.text(
            0.055,
            0.50,
            "PARAMETERS FOR AXIAL PILE CAPACITY MODEL - CPT BASED METHODS",
            rotation=270,
            fontsize=11.4,
            fontweight="bold",
            ha="center",
            va="center",
        )

        fig.text(
            0.095,
            0.50,
            "DRIVEN OPEN-ENDED CIRCULAR PILE\nWPA-01 Platform Site",
            rotation=270,
            fontsize=7.4,
            ha="center",
            va="center",
        )

        fig.text(
            0.025,
            0.50,
            "F136127MGT-ENG-RPT-003 02 | Piled Foundation Analyses Report\n"
            "for WPA-01 Platform Site\n\n"
            f"Plate 3.{4 + page_no}",
            rotation=270,
            fontsize=5.7,
            color="#003b71",
            ha="center",
            va="center",
        )

        fig.text(
            0.975,
            0.50,
            "PTTEP International Limited",
            rotation=270,
            fontsize=5.7,
            ha="center",
            va="center",
            color="#003b71",
        )

        # =========================
        # MAIN TABLE
        # Smaller table width and more balanced cell sizes.
        # =========================
        ax = fig.add_axes([0.135, 0.355, 0.735, 0.435])
        ax.axis("off")

        headers = [
            "Depth\nfrom-to\n[m]",
            "Ground\nunit\nname",
            "Ground\nunit\nbehaviour",
            "γ\n[kN/m3]",
            "cu\n[kPa]",
            "qc\n(qc_f / qc_eb)\n[MPa]",
            "δcv\n[deg]",
            "K0\n[-]",
            "flim\n[kPa]",
            "qlim\n[MPa]",
        ]

        def dash_if_none(value, fmt):
            if value is None:
                return "-"
            return fmt.format(value)

        table_rows = []
        for layer in layers_subset:
            depth = f'{layer["from_depth"]:.1f}\n{layer["to_depth"]:.1f}'
            soil = layer["soil_type"].title()
            behavior = layer["behavior"].title()

            gamma = "-"
            if layer["gamma_top"] is not None and layer["gamma_bot"] is not None:
                gamma = f'{layer["gamma_top"]:.1f}\n{layer["gamma_bot"]:.1f}'

            cu = "-"
            if layer["cu_top"] is not None and layer["cu_bot"] is not None:
                cu = f'{layer["cu_top"]:.0f}\n{layer["cu_bot"]:.0f}'

            qc = "-"
            if layer["qc_f"] is not None and layer["qc_eb"] is not None:
                qc = f'{layer["qc_f"] / 1000:.1f}\n{layer["qc_eb"] / 1000:.1f}'

            delta = dash_if_none(layer["delta_cv"], "{:.1f}")
            k0 = dash_if_none(layer["k0"], "{:.1f}")
            flim = dash_if_none(layer["flim"], "{:.0f}")
            qlim = "-" if layer["qlim"] is None else f'{layer["qlim"] / 1000:.1f}'

            table_rows.append([depth, soil, behavior, gamma, cu, qc, delta, k0, flim, qlim])

        table_data = [headers] + table_rows
        col_widths = [
            0.080,  # Depth
            0.150,  # Ground unit name
            0.130,  # Ground unit behaviour
            0.090,  # gamma
            0.090,  # cu
            0.140,  # qc
            0.090,  # delta_cv
            0.080,  # K0
            0.080,  # flim
            0.080,  # qlim
        ]

        table = ax.table(
            cellText=table_data,
            cellLoc="center",
            colWidths=col_widths,
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.2)
        set_table_font(table, body_size=7.2, header_size=6.8)

        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor("black")
            cell.set_linewidth(0.48)
            if r == 0:
                cell.set_text_props(weight="bold", ha="center", va="center")
                cell.get_text().set_fontsize(6.8)
                cell.set_facecolor("#f3f3f3")
                # Increase header row height so multi-line labels do not overlap.
                cell.set_height(0.135)
            else:
                cell.get_text().set_fontsize(7.2)
                cell.set_height(0.074)

        # Slightly thicker outer border.
        n_rows = len(table_data)
        n_cols = len(headers)
        for c in range(n_cols):
            table[(0, c)].set_linewidth(0.70)
            table[(n_rows - 1, c)].set_linewidth(0.70)
        for r in range(n_rows):
            table[(r, 0)].set_linewidth(0.70)
            table[(r, n_cols - 1)].set_linewidth(0.70)

        # =========================
        # DEFINITIONS / FOOTNOTES
        # Three framed boxes with tighter, more even proportions.
        # =========================
        box_y = 0.075
        box_h = 0.150
        left_ax = fig.add_axes([0.145, box_y, 0.330, box_h])
        mid_ax = fig.add_axes([0.495, box_y, 0.225, box_h])
        right_ax = fig.add_axes([0.740, box_y, 0.205, box_h])

        for info_ax in (left_ax, mid_ax, right_ax):
            info_ax.set_xticks([])
            info_ax.set_yticks([])
            info_ax.set_xlim(0, 1)
            info_ax.set_ylim(0, 1)
            info_ax.patch.set_alpha(0.0)
            for spine in info_ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.50)
                spine.set_edgecolor("black")

        left_ax.text(
            0.035,
            0.86,
            "Cohesive model     : API RP 2GEO (2011) and API RP 2GEO (2011) - Annex C\n"
            "                     (former API RP 2A - 1979)\n\n"
            "Frictional model   : API RP 2GEO (2011) CPT-based methods\n\n"
            "Rock model         : N.A.\n\n"
            "Porewater pressure : Hydrostatic from ground surface",
            fontsize=5.85,
            ha="left",
            va="top",
            linespacing=1.12,
        )

        mid_ax.text(
            0.075,
            0.86,
            "γ        : Total unit weight\n\n"
            "cu       : Undrained shear strength\n\n"
            "qc       : Cone resistance (pairs of values\n"
            "           denote qc for friction and end\n"
            "           bearing defined independently)",
            fontsize=5.85,
            ha="left",
            va="top",
            linespacing=1.12,
        )

        right_ax.text(
            0.075,
            0.86,
            "δcv      : Constant volume\n"
            "           interface friction angle\n\n"
            "K0       : Coefficient of lateral earth\n"
            "           pressure at rest\n\n"
            "flim     : Limiting unit skin friction\n\n"
            "qlim     : Limiting unit end bearing",
            fontsize=5.85,
            ha="left",
            va="top",
            linespacing=1.12,
        )

        return fig

    def make_report_intro_fig(D, pile_length, analysis_depth, WT, FS):
        """First page: explain what the program/report does and why."""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        # Logo
        try:
            base_dir = Path(__file__).resolve().parent
            logo_path = base_dir / "PTTEP_Logo.svg.png"
            logo_img = mpimg.imread(str(logo_path))
            logo_ax = fig.add_axes([0.73, 0.845, 0.11, 0.07])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")
            fig.text(0.78, 0.815, "PTTEP International Limited", ha="center", fontsize=7)
        except Exception:
            fig.text(0.78, 0.875, "PTTEP", ha="center", fontsize=18, fontweight="bold", color="#003b71")
            fig.text(0.78, 0.845, "PTTEP International Limited", ha="center", fontsize=7)

        fig.text(0.12, 0.88, "CPT-BASED AXIAL PILE CAPACITY CALCULATION REPORT", fontsize=12, fontweight="bold", ha="left")
        fig.text(0.12, 0.845, f"Driven Open-Ended Circular Pile - {pile_case_combo.get()}", fontsize=10, ha="left")
        fig.text(0.12, 0.820, "WPA-01 Platform Site", fontsize=9, ha="left")

        # Horizontal line
        ax.plot([0.12, 0.88], [0.795, 0.795], transform=fig.transFigure, color="black", linewidth=0.8)

        body = (
            "PROJECT\n"
            "WPA-01 Platform Site\n\n"
            "REPORT OBJECTIVE\n"
            "To evaluate axial pile capacity of driven open-ended circular steel piles using API RP 2GEO (2011) CPT-based methods. "
            "The output is prepared as a transparent calculation package for checking, comparison, and engineering review.\n\n"
            "SCOPE OF WORK\n"
            "The program imports layer-based soil parameters, calculates unit shaft resistance and end bearing resistance, and produces axial capacity profiles in both compression and tension.\n\n"
            "METHODS CONSIDERED\n"
            "- API Main Text Method: α-method for clay and β/Nq method for sand\n"
            "- Method 1: Simplified ICP-05\n"
            "- Method 2: Offshore UWA-05\n"
            "- Method 3: Fugro-05\n"
            "- Method 4: NGI-05\n\n"
            "REPORT OUTPUTS\n"
            "- Input parameter tables\n"
            "- Cone resistance profiles for shaft friction and end bearing\n"
            "- Ultimate axial pile capacity curves\n"
            "- Final compression and tension capacity summary\n\n"
            "BASIS OF CALCULATION\n"
            "Cohesive layers are evaluated using the API RP 2GEO cohesive model and Annex C reference. "
            "Frictional layers can be evaluated using either CPT-based methods or the API Main Text simplified β/Nq method. "
            "For API Main Text sand layers, relative density is estimated using a WPA-01/Fugro-calibrated CPT trend only for automatic selection of β and Nq, and API Table 1 limiting shaft friction and end bearing values are applied. "
            "Effective vertical stress is computed using effective unit weight based on the total unit weight input and hydrostatic porewater assumption."
        )

        fig.text(0.12, 0.745, body, fontsize=8.2, ha="left", va="top", linespacing=1.45, wrap=True)

        # Project data box
        info_ax = fig.add_axes([0.12, 0.095, 0.76, 0.155])
        info_ax.set_xticks([])
        info_ax.set_yticks([])
        info_ax.set_xlim(0, 1)
        info_ax.set_ylim(0, 1)
        for spine in info_ax.spines.values():
            spine.set_linewidth(0.6)
            spine.set_edgecolor("black")

        info_text = (
            f"Pile Case: {pile_case_combo.get()}\n"
            f"Pile Diameter, D: {D:.4f} m\n"
            f"Pile Length: {pile_length:.3f} m\n"
            f"Analysis Depth: {analysis_depth:.3f} m\n"
            f"Wall Thickness, WT: {WT:.4f} m\n"
            f"Factor of Safety: {FS:.2f}"
        )
        info_ax.text(0.03, 0.80, "Input Summary", fontsize=8.5, fontweight="bold", ha="left", va="top")
        info_ax.text(0.03, 0.60, info_text, fontsize=7.5, ha="left", va="top", linespacing=1.35)
        info_ax.text(0.62, 0.60, "Prepared output format:\n- A4 PDF report\n- Fugro/APICAP-style tables and plots\n- PTTEP-branded presentation layout", fontsize=7.5, ha="left", va="top", linespacing=1.35)

        fig.text(0.12, 0.045, "F136127MGT-ENG-RPT-003 02 | Piled Foundation Analyses Report for WPA-01 Platform Site", fontsize=6, ha="left", color="#003b71")
        fig.text(0.12, 0.030, "Introductory Page", fontsize=6, ha="left")
        return fig

    def make_calculation_summary_fig(D, pile_length, analysis_depth, WT, FS, layer_lines):
        """Final page: modern PTTEP-style calculation summary."""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        # =========================
        # THEME
        # =========================
        navy = "#003B71"
        blue = "#0056A6"
        sky = "#EAF3FF"
        pale = "#F6F9FD"
        line = "#D6E0EA"
        text = "#0F172A"
        muted = "#64748B"
        green = "#087A4B"
        amber = "#B7791F"
        red_soft = "#FCE8E8"
        green_soft = "#E8F7EE"
        amber_soft = "#FFF4DE"
        blue_soft = "#EAF3FF"

        # Header band
        ax.add_patch(plt.Rectangle((0.00, 0.932), 1.00, 0.068, transform=fig.transFigure, color=navy, zorder=0))
        ax.add_patch(plt.Rectangle((0.00, 0.920), 1.00, 0.012, transform=fig.transFigure, color=blue, zorder=0))

        # Logo top right
        try:
            base_dir = Path(__file__).resolve().parent
            logo_path = base_dir / "PTTEP_Logo.svg.png"
            if not logo_path.exists():
                alt_logo = base_dir / "PTTEP_Logo.svg(1).png"
                if alt_logo.exists():
                    logo_path = alt_logo
            logo_img = mpimg.imread(str(logo_path))
            logo_ax = fig.add_axes([0.795, 0.940, 0.125, 0.060])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")
        except Exception:
            fig.text(0.855, 0.966, "PTTEP", fontsize=15, fontweight="bold", color="white", ha="center", va="center")

        fig.text(0.105, 0.970, "CALCULATION SUMMARY", fontsize=16.5, fontweight="bold", color="white", ha="left", va="center")
        fig.text(0.105, 0.946, "CPT-Based Axial Pile Capacity Calculation Report", fontsize=8.8, color="#DCEBFF", ha="left", va="center")
        fig.text(
            0.105,
            0.925,
            f"Project: WPA-01 Platform Site   |   Pile Case: {pile_case_combo.get()}   |   Internal Engineering Tool",
            fontsize=6.5,
            color="#C9DEF6",
            ha="left",
            va="center",
        )
        fig.text(0.855, 0.925, "PTTEP International Limited", fontsize=6.5, color="#C9DEF6", ha="center", va="center")

        # Helpers
        def rect_card(x, y, w, h, face="white", edge=line, lw=0.8):
            # subtle shadow
            ax.add_patch(
                plt.Rectangle(
                    (x + 0.004, y - 0.004),
                    w,
                    h,
                    transform=fig.transFigure,
                    facecolor="#000000",
                    edgecolor="none",
                    alpha=0.065,
                    zorder=0,
                )
            )
            patch = plt.Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=face, edgecolor=edge, linewidth=lw)
            ax.add_patch(patch)
            return patch

        def card_title(x, y, title, subtitle=None):
            fig.text(x, y, title, fontsize=8.8, fontweight="bold", color=navy, ha="left", va="top")
            if subtitle:
                fig.text(x, y - 0.017, subtitle, fontsize=6.4, color=muted, ha="left", va="top")

        def kv_rows(x, y, rows, col_gap=0.150, line_h=0.028):
            for i, (k, v) in enumerate(rows):
                yy = y - i * line_h
                fig.text(x, yy, k, fontsize=7.0, color=muted, ha="left", va="center")
                fig.text(x + col_gap, yy, v, fontsize=7.1, color=text, ha="left", va="center", fontweight="bold")

        # =========================
        # COMPUTE SUMMARIES
        # =========================
        methods = ["API Main Text", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]
        summary_rows = []
        comp_values = []
        tens_values = []

        for method in methods:
            _, comp_summary, _ = calculate_layer_capacity(
                D=D, L=analysis_depth, WT=WT, FS=FS, method=method,
                layer_lines=layer_lines, loading_type="compression"
            )
            _, tens_summary, _ = calculate_layer_capacity(
                D=D, L=analysis_depth, WT=WT, FS=FS, method=method,
                layer_lines=layer_lines, loading_type="tension"
            )

            comp_qult = comp_summary["Qult"] / 1000
            comp_qallow = comp_summary["Qallow"] / 1000
            tens_qult = tens_summary["Qult"] / 1000
            tens_qallow = tens_summary["Qallow"] / 1000

            comp_values.append((method, comp_qult, comp_qallow))
            tens_values.append((method, tens_qult, tens_qallow))

            summary_rows.append([
                method,
                f"{comp_qult:.2f}",
                f"{comp_qallow:.2f}",
                f"{tens_qult:.2f}",
                f"{tens_qallow:.2f}",
            ])

        max_comp = max(comp_values, key=lambda x: x[1])
        min_comp = min(comp_values, key=lambda x: x[1])
        max_tens = max(tens_values, key=lambda x: x[1])
        min_tens = min(tens_values, key=lambda x: x[1])

        # =========================
        # KPI CARDS
        # =========================
        card_y = 0.785
        card_h = 0.092
        kpi_cards = [
            (0.105, card_y, 0.185, card_h, "Max Compression", f"{max_comp[1]:.2f} MN", max_comp[0], green, green_soft),
            (0.315, card_y, 0.185, card_h, "Min Compression", f"{min_comp[1]:.2f} MN", min_comp[0], amber, amber_soft),
            (0.525, card_y, 0.185, card_h, "Max Tension", f"{max_tens[1]:.2f} MN", max_tens[0], green, green_soft),
            (0.735, card_y, 0.160, card_h, "Factor of Safety", f"{FS:.2f}", "Applied to allowable", navy, blue_soft),
        ]
        for x, y, w, h, title, value, sub, color, face in kpi_cards:
            rect_card(x, y, w, h, face=face, edge=line, lw=0.8)
            ax.add_patch(plt.Rectangle((x, y + h - 0.006), w, 0.006, transform=fig.transFigure, color=color, zorder=3))
            fig.text(x + 0.018, y + h - 0.026, title, fontsize=6.9, color=muted, ha="left", va="top")
            fig.text(x + 0.018, y + 0.041, value, fontsize=16.0, color=color, ha="left", va="center", fontweight="bold")
            fig.text(x + 0.018, y + 0.014, sub, fontsize=6.4, color=muted, ha="left", va="bottom")

        # =========================
        # PILE / SETTINGS
        # =========================
        rect_card(0.105, 0.585, 0.790, 0.185, face="white", edge=line, lw=0.8)
        card_title(0.125, 0.748, "Pile and Analysis Information", "Geometry, selected penetration depth and calculation basis")

        fig.text(0.125, 0.706, "Pile Geometry", fontsize=7.3, color=navy, fontweight="bold", ha="left")
        fig.text(0.525, 0.706, "Analysis Settings", fontsize=7.3, color=navy, fontweight="bold", ha="left")

        left_rows = [
            ("D", f"{D:.4f} m"),
            ("WT", f"{WT:.4f} m"),
            ("Pile length", f"{pile_length:.3f} m"),
            ("Analysis depth", f"{analysis_depth:.3f} m"),
        ]
        right_rows = [
            ("Pile type", "Driven open-ended circular pile"),
            ("FS", f"{FS:.2f}"),
            ("Cohesive model", "API RP 2GEO / Annex C"),
            ("Frictional model", "API Main Text + CPT-based methods"),
        ]
        kv_rows(0.125, 0.685, left_rows, col_gap=0.135, line_h=0.024)
        kv_rows(0.525, 0.685, right_rows, col_gap=0.150, line_h=0.024)

        # =========================
        # TABLE
        # =========================
        fig.text(0.105, 0.535, "Method Comparison Summary", fontsize=9.5, fontweight="bold", color=navy, ha="left")
        fig.text(0.105, 0.518, "Ultimate and allowable capacity values at the selected analysis depth.", fontsize=6.7, color=muted, ha="left")

        table_ax = fig.add_axes([0.105, 0.290, 0.790, 0.205])
        table_ax.axis("off")

        headers = ["Method", "Qult Comp.\n[MN]", "Qallow Comp.\n[MN]", "Qult Tens.\n[MN]", "Qallow Tens.\n[MN]"]
        table = table_ax.table(
            cellText=[headers] + summary_rows,
            cellLoc="center",
            colWidths=[0.30, 0.175, 0.175, 0.175, 0.175],
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.3)

        comp_qult_col = 1
        comp_allow_col = 2
        tens_qult_col = 3
        tens_allow_col = 4

        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor(line)
            cell.set_linewidth(0.55)
            if r == 0:
                cell.set_facecolor(navy)
                cell.set_text_props(color="white", weight="bold", fontsize=7.0)
                cell.set_height(0.135)
            else:
                method_name = summary_rows[r - 1][0]
                base_face = "white" if r % 2 else "#F8FBFF"
                cell.set_facecolor(base_face)
                cell.set_text_props(color=text, fontsize=7.2)
                cell.set_height(0.110)
                if c == 0:
                    cell.set_text_props(color=navy, weight="bold", fontsize=7.2)

                # Highlight max/min for quick engineering review.
                if c in [comp_qult_col, comp_allow_col] and method_name == max_comp[0]:
                    cell.set_facecolor(green_soft)
                    cell.set_text_props(color=green, weight="bold", fontsize=7.2)
                elif c in [comp_qult_col, comp_allow_col] and method_name == min_comp[0]:
                    cell.set_facecolor(red_soft)
                    cell.set_text_props(color="#A33A3A", weight="bold", fontsize=7.2)
                elif c in [tens_qult_col, tens_allow_col] and method_name == max_tens[0]:
                    cell.set_facecolor(green_soft)
                    cell.set_text_props(color=green, weight="bold", fontsize=7.2)
                elif c in [tens_qult_col, tens_allow_col] and method_name == min_tens[0]:
                    cell.set_facecolor(red_soft)
                    cell.set_text_props(color="#A33A3A", weight="bold", fontsize=7.2)

        set_table_font(table, body_size=7.2, header_size=7.0)

        # =========================
        # ENGINEERING NOTES
        # =========================
        rect_card(0.105, 0.155, 0.790, 0.115, face=sky, edge="#BBD7F0", lw=0.8)
        card_title(0.125, 0.252, "Engineering Notes", "Summary interpretation for review and checking")

        fig.text(0.135, 0.220, f"✓ Highest Compression : {max_comp[0]} ({max_comp[1]:.2f} MN)", fontsize=7.1, color=text, ha="left", va="top")
        fig.text(0.525, 0.220, f"⚠ Lowest Compression  : {min_comp[0]} ({min_comp[1]:.2f} MN)", fontsize=7.1, color=text, ha="left", va="top")
        fig.text(0.135, 0.202, f"✓ Highest Tension     : {max_tens[0]} ({max_tens[1]:.2f} MN)", fontsize=7.1, color=text, ha="left", va="top")
        fig.text(0.525, 0.202, f"⚠ Lowest Tension      : {min_tens[0]} ({min_tens[1]:.2f} MN)", fontsize=7.1, color=text, ha="left", va="top")
        fig.text(
            0.135,
            0.182,
            "• Results should be reviewed together with soil profile, qc profile, Qshaft/Qbase breakdown,\n"
            "  method assumptions, and project-specific design basis.",
            fontsize=7.0,
            color=text,
            ha="left",
            va="top",
        )

        # =========================
        # METHOD STRIP
        # =========================
        rect_card(0.105, 0.088, 0.790, 0.045, face="white", edge=line, lw=0.7)
        fig.text(0.125, 0.115, "Methods considered", fontsize=7.2, color=navy, fontweight="bold", ha="left", va="center")
        fig.text(
            0.125,
            0.097,
            "API Main Text Method  •  Simplified ICP-05  •  Offshore UWA-05  •  Fugro-05  •  NGI-05",
            fontsize=6.8,
            color=text,
            ha="left",
            va="center",
        )

        # Footer divider
        ax.add_line(
            plt.Line2D(
                [0.105, 0.895],
                [0.068, 0.068],
                transform=fig.transFigure,
                color=line,
                linewidth=0.8,
            )
        )

        # Footer
        fig.text(0.105, 0.055, "PTTEP CPT-Based Axial Pile Capacity Calculator | Version 1.0", fontsize=5.9, ha="left", color=muted)
        fig.text(0.105, 0.042, "F136127MGT-ENG-RPT-003 02 | WPA-01 Platform Site", fontsize=6.0, ha="left", color=navy)
        fig.text(0.105, 0.029, "Calculation Summary", fontsize=5.9, ha="left", color=muted)
        fig.text(0.895, 0.029, "Generated by PTTEP Internal Engineering Tool", fontsize=5.8, ha="right", color=muted)

        return fig

    def export_pdf_report():
        if IS_DEMO_MODE:
            messagebox.showwarning(
                "Demo Mode",
                "Export PDF is available only for verified PTTEP users."
            )
            return

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
                # 1) Introductory page first: what this report does and why.
                fig = make_report_intro_fig(D, pile_length, analysis_depth, WT, FS)
                pdf.savefig(fig)
                plt.close(fig)

                # 2) Fugro/APICAP-style input parameter table pages.
                rows_per_page = 9
                for i in range(0, len(layers), rows_per_page):
                    page_layers = layers[i:i + rows_per_page]
                    page_no = i // rows_per_page + 1
                    fig = make_input_parameter_table_fig(page_layers, page_no=page_no)
                    pdf.savefig(fig)
                    plt.close(fig)

                # 3) qc profile page.
                fig = plot_qc_profile_to_current_fig(layers)
                pdf.savefig(fig)
                plt.close(fig)

                # 4) Capacity curves.
                fig = make_all_methods_curve_figure("compression")
                pdf.savefig(fig)
                plt.close(fig)

                fig = make_all_methods_curve_figure("tension")
                pdf.savefig(fig)
                plt.close(fig)

                # 5) Calculation summary at the end.
                fig = make_calculation_summary_fig(D, pile_length, analysis_depth, WT, FS, layer_lines)
                pdf.savefig(fig)
                plt.close(fig)

            messagebox.showinfo("Success", "Export PDF Report สำเร็จ")

        except Exception as e:
            messagebox.showerror("Error", f"Export PDF ไม่ได้\n\n{e}")

    def export_csv():
        if IS_DEMO_MODE:
            messagebox.showwarning(
                "Demo Mode",
                "Export CSV is available only for verified PTTEP users."
            )
            return

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
                    "Layer Qshaft",
                    "Cum. Qshaft",
                    "Qbase",
                    "Qult"
                ])
                writer.writerows(results)

            messagebox.showinfo("Success", "Export CSV สำเร็จ")

    root = tk.Tk()
    root.title("PTTEP CPT-Based Axial Pile Capacity Calculator")
    root.geometry("1580x880")
    root.minsize(1200, 700)
    root.configure(bg="#F4F7FB")

    if IS_DEMO_MODE:
        tk.Label(
            root,
            text="DEMO MODE  •  Export features are disabled",
            bg="#FFF4CE",
            fg="#8A5200",
            font=("Segoe UI", 9, "bold"),
            pady=4
        ).pack(fill="x")

    # =========================
    # MODERN UI THEME
    # =========================
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Modern.TButton",
        font=("Segoe UI", 9),
        padding=(10, 6),
        background="#FFFFFF",
        foreground="#0B1F3A",
        bordercolor="#D4DAE3",
        relief="flat"
    )
    style.map(
        "Modern.TButton",
        background=[("active", "#EAF2FF"), ("pressed", "#D8E8FF")],
        foreground=[("active", "#003B71")]
    )

    style.configure(
        "Primary.TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(10, 7),
        background="#003B71",
        foreground="white",
        bordercolor="#003B71",
        relief="flat"
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#005A9C"), ("pressed", "#002A52")],
        foreground=[("active", "white")]
    )

    style.configure(
        "Modern.TCombobox",
        padding=(6, 4),
        fieldbackground="white",
        background="white",
        foreground="#0B1F3A",
        arrowcolor="#003B71"
    )

    style.configure(
        "Modern.TEntry",
        padding=(6, 4),
        fieldbackground="white",
        foreground="#0B1F3A"
    )

    style.configure(
        "Treeview",
        font=("Segoe UI", 9),
        rowheight=24,
        background="white",
        fieldbackground="white",
        foreground="#0B1F3A",
        bordercolor="#E1E6EF",
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        background="#EAF2FF",
        foreground="#003B71",
        relief="flat"
    )
    style.map(
        "Treeview",
        background=[("selected", "#CFE4FF")],
        foreground=[("selected", "#0B1F3A")]
    )


    # Header bar
    # Uses only the PTTEP droplet icon from the full PTTEP logo image.
    header_frame = tk.Frame(root, bg="#003B71", height=100)
    header_frame.pack(fill="x", side="top")
    header_frame.pack_propagate(False)

    logo_frame = tk.Frame(
        header_frame,
        bg="#003B71",
        width=100,
        height=100
    )
    logo_frame.pack(side="left", padx=(30, 18), pady=0)
    logo_frame.pack_propagate(False)

    try:
        from PIL import Image, ImageTk
        from pathlib import Path

        base_dir = Path(__file__).resolve().parent

        logo_path = base_dir / "PTTEP_Logo.svg.png"
        if not logo_path.exists():
            logo_path = base_dir / "PTTEP_Logo.svg(1).png"

        logo_img = Image.open(logo_path).convert("RGBA")

        # Crop out only the lower PTTEP wordmark, while keeping the full droplet shape.
        # thumbnail() preserves aspect ratio so the droplet will not look thin/stretched.
        w, h = logo_img.size
        logo_img = logo_img.crop((
            int(w * 0.18),  # left
            0,              # top
            int(w * 0.82),  # right
            int(h * 0.72)   # bottom: removes PTTEP wordmark but keeps full droplet
        ))
        logo_img.thumbnail((72, 72), Image.LANCZOS)

        header_logo = ImageTk.PhotoImage(logo_img)

        logo_label = tk.Label(
            logo_frame,
            image=header_logo,
            bg="#003B71",
            bd=0,
            highlightthickness=0
        )
        logo_label.image = header_logo
        logo_label.pack(expand=True)

    except Exception as e:
        print("Logo load error:", e)
        tk.Label(
            logo_frame,
            text="PTTEP",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#003B71"
        ).pack(expand=True)

    title_frame = tk.Frame(header_frame, bg="#003B71")
    title_frame.pack(
        side="left",
        fill="both",
        expand=True,
        pady=(18, 12)
    )

    tk.Label(
        title_frame,
        text="PTTEP CPT-Based Axial Pile Capacity Calculator",
        font=("Segoe UI", 18, "bold"),
        fg="white",
        bg="#003B71"
    ).pack(anchor="w")

    tk.Label(
        title_frame,
        text=(
            f"Version {APP_VERSION}    •    "
            "Authorized Internal Use Only    •    "
            "API RP 2GEO CPT-Based Methods"
        ),
        font=("Segoe UI", 9),
        fg="#C7D9F2",
        bg="#003B71"
    ).pack(anchor="w", pady=(4, 0))

    # Thin divider under the header for a cleaner engineering-software look.
    tk.Frame(
        root,
        height=2,
        bg="#0056A6"
    ).pack(fill="x")

    main_frame = tk.Frame(root, bg="#F4F7FB")
    main_frame.pack(fill="both", expand=True, padx=18, pady=16)

    def make_card(parent, title, width=None):
        outer = tk.Frame(parent, bg="#DDE5F0")
        inner = tk.Frame(outer, bg="white", padx=12, pady=12)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(
            inner,
            text=title,
            font=("Segoe UI", 10, "bold"),
            fg="#003B71",
            bg="white"
        ).pack(anchor="w", pady=(0, 8))
        if width:
            outer.configure(width=width)
            outer.pack_propagate(False)
        return outer, inner

    # =========================
    # SCROLLABLE LEFT SIDEBAR
    # Fixes small-screen issue where lower buttons such as Export PDF / Export CSV
    # can be hidden below the window.
    # =========================
    left_container = tk.Frame(main_frame, bg="#F4F7FB", width=250)
    left_container.pack(side="left", fill="y", padx=(0, 14))
    left_container.pack_propagate(False)

    left_canvas = tk.Canvas(
        left_container,
        width=240,
        bg="#F4F7FB",
        highlightthickness=0,
        bd=0
    )

    left_scrollbar = ttk.Scrollbar(
        left_container,
        orient="vertical",
        command=left_canvas.yview
    )

    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    left_scrollbar.pack(side="right", fill="y")
    left_canvas.pack(side="left", fill="both", expand=True)

    scroll_frame = tk.Frame(left_canvas, bg="#F4F7FB")
    scroll_window = left_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def _on_sidebar_configure(event=None):
        left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        left_canvas.itemconfig(scroll_window, width=left_canvas.winfo_width())

    scroll_frame.bind("<Configure>", _on_sidebar_configure)
    left_canvas.bind("<Configure>", _on_sidebar_configure)

    def _on_sidebar_mousewheel(event):
        # Windows / macOS mousewheel support.
        widget_under_mouse = left_canvas.winfo_containing(event.x_root, event.y_root)
        if widget_under_mouse is not None:
            try:
                if str(widget_under_mouse).startswith(str(left_canvas)) or str(widget_under_mouse).startswith(str(scroll_frame)):
                    left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass


    left_card, left_frame = make_card(scroll_frame, "Pile Input")
    left_card.pack(fill="both", expand=True)

    middle_card, middle_frame = make_card(main_frame, "Layer Input and Calculation")
    middle_card.pack(side="left", fill="both", expand=True, padx=(0, 14))

    right_card, right_frame = make_card(main_frame, "Summary Result", width=285)
    right_card.pack(side="right", fill="y")

    tk.Label(left_frame, text="Pile Case", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    pile_case_combo = ttk.Combobox(
        left_frame,
        values=["Custom", "54-in OD", "66-in OD"],
        width=17,
        style="Modern.TCombobox"
    )
    pile_case_combo.pack(fill="x", pady=(3, 8))
    pile_case_combo.current(1)

    tk.Label(left_frame, text="Pile Diameter, D (m)", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    entry_diameter = ttk.Entry(left_frame, width=20, style="Modern.TEntry")
    entry_diameter.pack(fill="x", pady=4)
    entry_diameter.insert(0, "1.3716")

    tk.Label(left_frame, text="Pile Length, Ltotal (m)", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    entry_length = ttk.Entry(left_frame, width=20, style="Modern.TEntry")
    entry_length.pack(fill="x", pady=4)
    entry_length.insert(0, "173.563")

    tk.Label(left_frame, text="Analysis Depth, Lembed (m)", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    entry_analysis_depth = ttk.Entry(left_frame, width=20, style="Modern.TEntry")
    entry_analysis_depth.pack(fill="x", pady=4)
    entry_analysis_depth.insert(0, "157.5")

    tk.Label(left_frame, text="Wall Thickness, WT (m)", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    entry_wt = ttk.Entry(left_frame, width=20, style="Modern.TEntry")
    entry_wt.pack(fill="x", pady=4)
    entry_wt.insert(0, "0.0445")

    pile_case_combo.bind("<<ComboboxSelected>>", apply_pile_case)

    tk.Label(left_frame, text="Factor of Safety", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    entry_fs = ttk.Entry(left_frame, width=20, style="Modern.TEntry")
    entry_fs.pack(fill="x", pady=4)
    entry_fs.insert(0, "2.0")

    tk.Label(left_frame, text="Analysis Method", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    method_combo = ttk.Combobox(
        left_frame,
        values=["API Main Text", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"],
        width=17,
        style="Modern.TCombobox"
    )
    method_combo.pack(fill="x", pady=(3, 8))
    method_combo.current(2)

    tk.Label(left_frame, text="Loading Type", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    loading_combo = ttk.Combobox(
        left_frame,
        values=["Compression", "Tension"],
        width=17,
        style="Modern.TCombobox"
    )
    loading_combo.pack(fill="x", pady=(3, 8))
    loading_combo.current(0)

    ttk.Button(left_frame, text="Import CSV", width=24, command=import_csv, style="Modern.TButton").pack(fill="x", pady=(8, 5))
    ttk.Button(left_frame, text="Calculate", width=24, command=calculate, style="Primary.TButton").pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Report qc Profile", width=24, style="Modern.TButton", command=show_report_qc_profile).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Single Method Curve", width=24, style="Modern.TButton", command=show_capacity_curve).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="All Methods Compression", width=24, style="Modern.TButton", command=lambda: show_all_methods_curve("compression")).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="All Methods Tension", width=24, style="Modern.TButton", command=lambda: show_all_methods_curve("tension")).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Export PDF Report", width=24, style="Modern.TButton", command=export_pdf_report).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Export CSV", width=24, style="Modern.TButton", command=export_csv).pack(fill="x", pady=4)

    tk.Label(
        middle_frame,
        text="Format: from_depth,to_depth,soil_type,behavior,gamma_top,gamma_bot,cu_top,cu_bot,qc_f,qc_eb,delta_cv,k0,flim,qlim",
        bg="white",
        fg="#64748B",
        font=("Segoe UI", 8)
    ).pack(anchor="w")

    layer_text = tk.Text(middle_frame, height=13, width=120, bg="#FBFDFF", fg="#0B1F3A", insertbackground="#003B71", relief="flat", bd=1, font=("Consolas", 9))
    layer_text.pack(fill="x", pady=5)

    layer_text.insert(tk.END, """0,3,clay,cohesive,16.4,16.4,1,9,,,,,,
3,7.9,clay,cohesive,16.4,16.4,9,14,,,,,,
7.9,10.8,clay,cohesive,18.2,18.2,16,16,,,,,,
10.8,14,clay,cohesive,18.4,18.4,22,25,,,,,,
14,20.9,clay,cohesive,17.0,17.0,25,40,,,,,,
20.9,27.4,clay,cohesive,17.7,17.7,42,50,,,,,,
27.4,32.5,clay,cohesive,17.4,17.4,55,65,,,,,,
32.5,36.8,clay,cohesive,17.4,17.4,65,65,,,,,,
36.8,47,clay,cohesive,18.0,18.0,65,80,,,,,,
47,50,clay,cohesive,18.0,18.0,85,85,,,,,,
50,51.6,sand,frictional,18.3,18.3,,,8,9,28.8,1.0,,
51.6,57.7,sand,frictional,19.2,19.2,,,27,18,26.1,1.0,,
57.7,61,sand,frictional,19.2,19.2,,,26,26,26.1,1.0,,
61,64,sand,frictional,18.7,18.7,,,10.5,10.5,28.8,1.0,,
64,66.7,sand,frictional,18.7,18.7,,,17,17,28.8,1.0,,
66.7,68.5,sand,frictional,20.0,20.0,,,26,40,26.1,1.0,,
68.5,71,sand,frictional,20.0,20.0,,,40,33,26.1,1.0,,
71,74,sand,frictional,20.0,20.0,,,24,24,26.1,1.0,,
74,77.3,sand,frictional,20.0,20.0,,,31.5,31.5,26.1,1.0,,
77.3,83,sand,frictional,19.2,19.2,,,23,25,26.1,1.0,,
83,95.2,sand,frictional,20.1,20.1,,,30,30,26.1,1.0,,
95.2,102.6,sand,frictional,18.7,18.7,,,16,16,28.8,1.0,,
102.6,106.8,clay,cohesive,18.9,18.9,180,205,,,,,,
106.8,108.8,sand,frictional,20.0,20.0,,,20,20,28.8,1.0,,
108.8,110.8,clay,cohesive,20.0,20.0,160,160,,,,,,
110.8,112,sand,frictional,18.1,18.1,,,18,18,28.8,1.0,,
112,113.7,sand/clay,frictional,18.1,18.1,,,12,12,28.8,1.0,,2.2
113.7,114.8,clay,cohesive,19.1,19.1,230,230,,,,,,
114.8,115.9,sand,frictional,20.0,20.0,,,33,33,28.8,1.0,,
115.9,116.9,sand/clay,frictional,19.3,19.3,,,8,8,28.8,1.0,,2.1
116.9,118.8,sand,frictional,19.1,19.1,,,17,17,28.8,1.0,,
118.8,123.5,silt,frictional,19.1,19.1,,,11,11,28.8,1.0,,
123.5,125.5,sand,frictional,19.1,19.1,,,14.5,14.5,28.8,1.0,,
125.5,129.6,silt/clay,frictional,19.8,19.8,,,8,8,28.8,1.0,,2.0
129.6,140,clay,cohesive,19.5,19.5,250,250,,,,,,
140,141.7,sand,frictional,19.5,19.5,,,4.7,4.7,28.8,1.0,,
141.7,150,clay,cohesive,18.5,18.5,275,350,,,,,,
150,152,silt,frictional,20.0,20.0,,,24,24,28.8,1.0,,
152,157.5,clay,cohesive,18.5,18.5,350,350,,,,,,""")

    columns = (
        "depth_range", "soil", "behavior", "gamma", "gamma_eff", "p0_layer", "cum_p0", "cu",
        "qc_f", "qc_eb", "delta", "k0", "flim", "qlim",
        "used", "unit_shaft", "qshaft_layer", "qshaft_cum", "qbase", "qult"
    )

    table = ttk.Treeview(middle_frame, columns=columns, show="headings", height=17)

    headings = {
        "depth_range": "Depth",
        "soil": "Soil",
        "behavior": "Behaviour",
        "gamma": "γ",
        "gamma_eff": "γ'",
        "p0_layer": "p'0 layer",
        "cum_p0": "Cum. p'0",
        "cu": "cu",
        "qc_f": "qc,f",
        "qc_eb": "qc,eb",
        "delta": "δcv",
        "k0": "K0",
        "flim": "flim",
        "qlim": "qlim",
        "used": "Used",
        "unit_shaft": "Unit Shaft",
        "qshaft_layer": "Layer Qshaft",
        "qshaft_cum": "Cum. Qshaft",
        "qbase": "Qbase",
        "qult": "Qult"
    }

    widths = {
        "depth_range": 90,
        "soil": 80,
        "behavior": 80,
        "gamma": 50,
        "gamma_eff": 55,
        "p0_layer": 80,
        "cum_p0": 80,
        "cu": 50,
        "qc_f": 50,
        "qc_eb": 50,
        "delta": 50,
        "k0": 45,
        "flim": 55,
        "qlim": 55,
        "used": 60,
        "unit_shaft": 85,
        "qshaft_layer": 95,
        "qshaft_cum": 100,
        "qbase": 85,
        "qult": 85
    }

    for col in columns:
        table.heading(col, text=headings[col])
        table.column(col, width=widths[col], anchor="center", stretch=False)

    table_xscroll = ttk.Scrollbar(middle_frame, orient="horizontal", command=table.xview)
    table.configure(xscrollcommand=table_xscroll.set)
    table.pack(fill="both", expand=True, pady=(10, 0))
    table_xscroll.pack(fill="x", pady=(0, 10))

    # =========================
    # MODERN SUMMARY PANEL - SCROLLABLE
    # =========================
    # Summary card area can be taller than small laptop screens.
    # Put all summary cards inside a scrollable canvas so Qshaft / Qbase
    # will not be clipped after pressing Calculate.
    summary_canvas = tk.Canvas(
        right_frame,
        bg="white",
        highlightthickness=0,
        bd=0
    )
    summary_canvas.pack(side="left", fill="both", expand=True)

    summary_scrollbar = ttk.Scrollbar(
        right_frame,
        orient="vertical",
        command=summary_canvas.yview
    )
    summary_scrollbar.pack(side="right", fill="y")

    summary_canvas.configure(yscrollcommand=summary_scrollbar.set)

    summary_inner = tk.Frame(summary_canvas, bg="white")
    summary_window = summary_canvas.create_window(
        (0, 0),
        window=summary_inner,
        anchor="nw"
    )

    def _on_summary_configure(event=None):
        summary_canvas.configure(scrollregion=summary_canvas.bbox("all"))
        summary_canvas.itemconfig(summary_window, width=summary_canvas.winfo_width())

    summary_inner.bind("<Configure>", _on_summary_configure)
    summary_canvas.bind("<Configure>", _on_summary_configure)

    def _on_summary_mousewheel(event):
        # Same scrolling behavior as the left Pile Input sidebar.
        # It scrolls only when the mouse is over the Summary Result panel.
        widget_under_mouse = summary_canvas.winfo_containing(event.x_root, event.y_root)
        if widget_under_mouse is not None:
            try:
                if str(widget_under_mouse).startswith(str(summary_canvas)) or str(widget_under_mouse).startswith(str(summary_inner)):
                    summary_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass


    def _on_global_mousewheel(event):
        """
        Route mouse wheel scrolling to the panel currently under the mouse.
        This fixes the conflict where left sidebar and summary panel both used bind_all().
        """
        widget_under_mouse = root.winfo_containing(event.x_root, event.y_root)
        if widget_under_mouse is None:
            return

        widget_path = str(widget_under_mouse)

        try:
            # Left Pile Input sidebar
            if widget_path.startswith(str(left_canvas)) or widget_path.startswith(str(scroll_frame)):
                left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return

            # Right Summary Result panel
            if widget_path.startswith(str(summary_canvas)) or widget_path.startswith(str(summary_inner)):
                summary_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return

        except Exception:
            pass

    root.bind_all("<MouseWheel>", _on_global_mousewheel)

    def add_kpi_card(parent, title, value_key, subtitle=""):
        card = tk.Frame(parent, bg="#E1E8F2")
        card.pack(fill="x", pady=(0, 8), padx=(0, 4))

        inner = tk.Frame(card, bg="#F8FBFF", padx=10, pady=7)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(
            inner,
            text=title,
            bg="#F8FBFF",
            fg="#64748B",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        summary_vars[value_key] = tk.StringVar(value="-")
        tk.Label(
            inner,
            textvariable=summary_vars[value_key],
            bg="#F8FBFF",
            fg="#003B71",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(1, 0))

        if subtitle:
            tk.Label(
                inner,
                text=subtitle,
                bg="#F8FBFF",
                fg="#64748B",
                font=("Segoe UI", 7)
            ).pack(anchor="w")

    def add_info_section(parent, title, rows):
        section = tk.Frame(parent, bg="#E1E8F2")
        section.pack(fill="x", pady=(0, 8), padx=(0, 4))

        inner = tk.Frame(section, bg="#FFFFFF", padx=10, pady=8)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(
            inner,
            text=title,
            bg="#FFFFFF",
            fg="#003B71",
            font=("Segoe UI", 8, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        for i, (label, key) in enumerate(rows, start=1):
            tk.Label(
                inner,
                text=label,
                bg="#FFFFFF",
                fg="#64748B",
                font=("Segoe UI", 8)
            ).grid(row=i, column=0, sticky="w", pady=1)

            summary_vars[key] = tk.StringVar(value="-")
            tk.Label(
                inner,
                textvariable=summary_vars[key],
                bg="#FFFFFF",
                fg="#0B1F3A",
                font=("Segoe UI", 8, "bold")
            ).grid(row=i, column=1, sticky="e", pady=1, padx=(8, 0))

        inner.grid_columnconfigure(1, weight=1)

    add_info_section(
        summary_inner,
        "PROJECT",
        [
            ("Pile Case", "pile_case"),
            ("Method", "method"),
            ("Loading", "loading"),
        ]
    )

    add_info_section(
        summary_inner,
        "PILE GEOMETRY",
        [
            ("D", "D"),
            ("Pile Length", "pile_length"),
            ("Analysis Depth", "analysis_depth"),
            ("WT", "WT"),
            ("FS", "FS"),
        ]
    )

    add_info_section(
        summary_inner,
        "BASE / SOIL MODEL",
        [
            ("Base Model", "base_model"),
            ("Ap", "Ap"),
            ("Perimeter", "perimeter"),
            ("Ar", "Ar"),
            ("qc_eb,av", "qc_eb"),
            ("qbase unit", "qbase_unit"),
        ]
    )

    add_kpi_card(summary_inner, "ULTIMATE CAPACITY", "Qult", "Qult")
    add_kpi_card(summary_inner, "ALLOWABLE CAPACITY", "Qallow", "Qallow")
    add_kpi_card(summary_inner, "SHAFT CAPACITY", "Qshaft", "Qshaft")
    add_kpi_card(summary_inner, "BASE CAPACITY", "Qbase", "Qbase")



    root.mainloop()
