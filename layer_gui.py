import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
import csv
import math
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =========================
# REPORT FONT SETTINGS
# Pick an installed font only, so matplotlib will not spam findfont warnings.
# On Windows this usually selects Arial / Segoe UI / Calibri.
# =========================
from matplotlib import font_manager


def resource_path(relative_path):
    """
    Return the correct path for files bundled by PyInstaller.
    Works both when running as .py and when running as .exe.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def _pick_report_font():
    preferred = ["Arial", "Helvetica Neue", "Segoe UI", "Calibri", "Tahoma", "DejaVu Sans"]
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
    layer_value,
    effective_stress_at_depth,
    unit_shaft_frictional,
    end_bearing_cohesive,
    integrate_layer_shaft,
    set_annex_c_high_plastic_ratio_range
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
        text="Interactive Axial Pile Calculator",
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
    # Development default
    email_entry.insert(0, "zWachirawitP@pttep.com")

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
    # Development default
    key_entry.insert(0, LICENSE_KEY)

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




# =========================
# MODERN SCROLLBAR STYLE
# =========================
def configure_modern_scrollbar_style(root):
    try:
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Modern.Vertical.TScrollbar",
            background="#2F80ED",
            darkcolor="#2F80ED",
            lightcolor="#2F80ED",
            troughcolor="#EEF4FB",
            bordercolor="#EEF4FB",
            arrowcolor="#2F80ED",
            relief="flat",
            width=10,
            arrowsize=10,
        )
        style.map(
            "Modern.Vertical.TScrollbar",
            background=[("active", "#1C64D1")],
            arrowcolor=[("active", "#1C64D1")]
        )

        style.configure(
            "Modern.Horizontal.TScrollbar",
            background="#2F80ED",
            darkcolor="#2F80ED",
            lightcolor="#2F80ED",
            troughcolor="#EEF4FB",
            bordercolor="#EEF4FB",
            arrowcolor="#2F80ED",
            relief="flat",
            width=10,
            arrowsize=10,
        )
    except Exception:
        pass

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
            cohesive_model = cohesive_combo.get()
            loading_type = loading_combo.get().lower()

            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

            rows, summary, layers = calculate_layer_capacity(
                D=D,
                L=analysis_depth,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
                cohesive_model=cohesive_model
            )

            table.delete(*table.get_children())

            # Per-row breakdown for engineering discussion:
            # Layer Qshaft = shaft contribution of that layer only
            # Cum. Qshaft = accumulated shaft resistance down to that depth
            # Unit End Bearing = qbase unit resistance at that depth
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
                        loading_type=loading_type,
                        cohesive_model=cohesive_model
                    )
                    tip_summary_cache[depth_key] = tip_summary
                return tip_summary_cache[depth_key]

            for row in rows:
                try:
                    row_to_depth = float(str(row["depth_range"]).split("-")[-1])
                    tip_summary = get_tip_summary_at_depth(row_to_depth)
                    cum_qshaft = tip_summary["Qshaft"]
                    qbase_at_depth = tip_summary["Qbase"]
                    q_unit_base_at_depth = tip_summary.get("q_unit_base")
                    qult_at_depth = tip_summary["Qult"]
                except Exception:
                    cum_qshaft = None
                    qbase_at_depth = None
                    q_unit_base_at_depth = None
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
                    "-" if row.get("alpha") is None else f'{row["alpha"]:.3f}',
                    f'{row["unit_shaft"]:.2f}',
                    "-" if q_unit_base_at_depth is None else f'{q_unit_base_at_depth:.2f}',
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
                cohesive_model=cohesive_model,
                loading_type=summary["loading_type"].capitalize(),
                summary=summary,
                qc_eb_text=qc_eb_text,
                layers=layers,
                layer_lines=layer_lines
            )

        except Exception as e:
            messagebox.showerror("Error", f"ข้อมูลผิดหรือกรอกไม่ครบ\n\n{e}")


    def build_method_advisor_v4(D, analysis_depth, WT, FS, layers, layer_lines, loading_type, cohesive_model):
        """
        Engineering Method Selection Advisor v4.
        The recommendation is based on:
        1) site condition / soil profile,
        2) method applicability,
        3) calculated capacity comparison,
        4) project verification basis.

        Important: the lowest calculated method is treated as a governing check only after
        confirming that the method is applicable to the project condition.
        """
        methods = ["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]

        # -----------------------------
        # 1) Site assessment
        # -----------------------------
        total_thk = cohesive_thk = frictional_thk = 0.0
        layer_changes = 0
        previous_behavior = None
        qc_values = []
        cu_values = []
        tip_layer = None

        for layer in layers:
            z1 = max(float(layer.get("from_depth", 0.0)), 0.0)
            z2 = min(float(layer.get("to_depth", 0.0)), analysis_depth)
            if z2 <= z1:
                continue

            thk = z2 - z1
            total_thk += thk
            behavior = str(layer.get("behavior", "")).lower()

            if behavior == "cohesive":
                cohesive_thk += thk
            elif behavior == "frictional":
                frictional_thk += thk

            if previous_behavior is not None and behavior != previous_behavior:
                layer_changes += 1
            previous_behavior = behavior

            qcf = layer.get("qc_f")
            qceb = layer.get("qc_eb")
            if qcf is not None:
                qc_values.append(float(qcf) / 1000.0)
            if qceb is not None:
                qc_values.append(float(qceb) / 1000.0)

            cu = layer.get("cu")
            if cu is not None:
                cu_values.append(float(cu))

            if z1 <= analysis_depth <= z2:
                tip_layer = layer

        if tip_layer is None and layers:
            tip_layer = [ly for ly in layers if float(ly.get("from_depth", 0.0)) < analysis_depth]
            tip_layer = tip_layer[-1] if tip_layer else layers[-1]

        cohesive_ratio = cohesive_thk / total_thk if total_thk > 0 else 0.0
        frictional_ratio = frictional_thk / total_thk if total_thk > 0 else 0.0
        tip_soil = str(tip_layer.get("soil_type", "unknown")) if tip_layer else "unknown"
        tip_behavior = str(tip_layer.get("behavior", "unknown")) if tip_layer else "unknown"
        dominant_shaft = "cohesive" if cohesive_ratio >= frictional_ratio else "frictional"
        interbedded = layer_changes >= 3 or (cohesive_ratio > 0.25 and frictional_ratio > 0.25)
        avg_qc = sum(qc_values) / len(qc_values) if qc_values else None
        max_qc = max(qc_values) if qc_values else None
        avg_cu = sum(cu_values) / len(cu_values) if cu_values else None

        # -----------------------------
        # 2) Capacity comparison
        # -----------------------------
        capacities = {}
        for m in methods:
            try:
                _rows, _summary, _layers = calculate_layer_capacity(
                    D=D,
                    L=analysis_depth,
                    WT=WT,
                    FS=FS,
                    method=m,
                    layer_lines=layer_lines,
                    loading_type=str(loading_type).lower(),
                    cohesive_model=cohesive_model,
                )
                capacities[m] = float(_summary.get("Qult", 0.0)) / 1000.0  # kN -> MN
            except Exception:
                capacities[m] = None

        valid_caps = {m: q for m, q in capacities.items() if q is not None and q > 0}
        lowest_method = min(valid_caps, key=valid_caps.get) if valid_caps else "-"
        lowest_value = valid_caps.get(lowest_method)
        max_value = max(valid_caps.values()) if valid_caps else None
        min_value = min(valid_caps.values()) if valid_caps else None
        mean_value = (sum(valid_caps.values()) / len(valid_caps)) if valid_caps else None
        spread_pct = ((max_value - min_value) / mean_value * 100.0) if mean_value and mean_value > 0 else None

        # -----------------------------
        # 3) Method applicability matrix
        # -----------------------------
        # The program is designed for offshore driven open-ended steel pipe piles.
        project_basis_fugro = True
        offshore_driven_pile = True
        has_sand = frictional_ratio > 0.10
        has_clay = cohesive_ratio > 0.10

        applicability = {}
        why = {}

        applicability["API Main Text"] = "Applicable"
        why["API Main Text"] = "General API clay/sand framework; directly handles cu-based clay shaft/base and API main text sand calculation."

        applicability["API RP 2A (1979-1986)"] = "Comparison"
        why["API RP 2A (1979-1986)"] = "Legacy API method retained for historical comparison, reassessment, and project specifications that explicitly require the older design basis."

        applicability["ISO 19901-4:2025"] = "Applicable" if has_sand else "Check only"
        why["ISO 19901-4:2025"] = "Unified CPT method for axial shaft and base resistance in applicable frictional layers; cohesive layers use the selected clay model."

        applicability["ICP-05"] = "Applicable" if has_sand else "Check only"
        why["ICP-05"] = "CPT-based method mainly useful for frictional layers; compare when sand/silty sand layers contribute to shaft or base."

        applicability["UWA-05"] = "Applicable" if has_sand or interbedded else "Check only"
        why["UWA-05"] = "Offshore CPT-based method; useful comparison for driven piles in sand and interbedded offshore profiles."

        applicability["Fugro-05"] = "Applicable" if offshore_driven_pile and has_sand else "Check only"
        why["Fugro-05"] = "Offshore CPT-based method; consistent with reference-report project verification and driven-pile design workflow."

        applicability["NGI-05"] = "Comparison"
        why["NGI-05"] = "Useful as an additional offshore CPT-based comparison method, especially for layered/deep profiles."

        # -----------------------------
        # 4) Final recommendation logic
        # -----------------------------
        primary = None
        secondary = []
        recommendation_reasons = []

        # Main decision: do not select the lowest value alone; select the lowest applicable method
        # when it is also compatible with offshore driven pile / CPT-based design practice.
        cpt_applicable = {"ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"}

        if lowest_method == "Fugro-05" and applicability.get("Fugro-05") == "Applicable" and project_basis_fugro:
            primary = "Fugro-05"
            recommendation_reasons += [
                "Fugro-05 is applicable to the offshore driven pile CPT-based workflow.",
                "Fugro-05 is consistent with the project verification basis used for comparison.",
                "Fugro-05 also provides the lowest calculated ultimate capacity among the applicable methods.",
            ]
            secondary = ["API Main Text clay model", "API RP 2A (1979-1986)", "ICP-05", "UWA-05", "NGI-05"]

        elif lowest_method in cpt_applicable and has_sand and applicability.get(lowest_method) in ("Applicable", "Comparison"):
            primary = lowest_method
            recommendation_reasons += [
                f"{lowest_method} is an applicable CPT-based method for the frictional portions of the profile.",
                f"{lowest_method} provides the lowest calculated ultimate capacity among applicable CPT-based methods.",
                "Use API clay model for cohesive layers and review all CPT methods as comparison.",
            ]
            secondary = [m for m in methods if m != primary]

        elif tip_behavior == "cohesive" and cohesive_ratio >= 0.60:
            primary = "API Main Text clay model"
            recommendation_reasons += [
                "Pile tip terminates in cohesive soil.",
                "Cohesive layers dominate the embedded length and clay base resistance follows cu-based calculation.",
                "CPT-based sand methods should remain comparison checks for any frictional layers.",
            ]
            secondary = ["Fugro-05", "UWA-05", "ICP-05", "NGI-05"]

        elif has_sand and frictional_ratio >= 0.60:
            primary = "Fugro-05"
            recommendation_reasons += [
                "Frictional soil contributes significantly to shaft/base resistance.",
                "Fugro-05 is applicable for offshore CPT-based driven pile design and project verification.",
                "Confirm with ICP-05 and UWA-05 comparison results.",
            ]
            secondary = ["ICP-05", "UWA-05", "NGI-05", "API Main Text", "API RP 2A (1979-1986)"]

        else:
            primary = "Engineering review"
            recommendation_reasons += [
                "The profile is mixed and no single method should be selected automatically.",
                "Use method applicability plus capacity comparison to select the design basis.",
            ]
            secondary = methods

        if str(loading_type).lower().startswith("tension"):
            recommendation_reasons.append("For tension loading, base resistance is not normally included; shaft resistance controls the recommendation.")

        warning_items = []
        if spread_pct is not None and spread_pct > 20.0:
            warning_items.append(f"Large method spread ({spread_pct:.1f}%). Review soil parameters, qc profiles, and layer-by-layer shaft/base contribution.")
        warning_items.append("Lowest capacity is a governing check, not an automatic method selection unless the method is also applicable.")
        warning_items.append("Do not mix shaft resistance from one method with end bearing from another method.")

        site_basis_lines = [
            f"Pile type: Driven open-ended steel pipe",
            f"Loading: {str(loading_type).capitalize()}",
            f"Pile tip: {tip_soil} ({tip_behavior})",
            f"Dominant shaft: {dominant_shaft}",
            f"Soil mix: C {cohesive_ratio*100:.0f}% / F {frictional_ratio*100:.0f}%",
            f"Interbedded: {'Yes' if interbedded else 'No'} ({layer_changes} changes)",
        ]
        if avg_qc is not None:
            site_basis_lines.append(f"qc avg/max: {avg_qc:.1f} / {max_qc:.1f} MPa")
        if avg_cu is not None:
            site_basis_lines.append(f"cu avg: {avg_cu:.0f} kPa")

        capacity_lines = []
        for m in methods:
            q = capacities.get(m)
            capacity_lines.append(f"{m}: {'-' if q is None else f'{q:.1f} MN'}")

        applicability_lines = []
        for m in methods:
            applicability_lines.append(f"{m}: {applicability[m]}")

        secondary_clean = []
        for m in secondary:
            if m not in secondary_clean and m != primary:
                secondary_clean.append(m)

        return {
            "primary_method": primary,
            "secondary_methods": ", ".join(secondary_clean[:4]) if secondary_clean else "-",
            "lowest_method": lowest_method if lowest_method else "-",
            "lowest_capacity": "-" if lowest_value is None else f"{lowest_method} ({lowest_value:.1f} MN)",
            "spread": "-" if spread_pct is None else f"{spread_pct:.1f}%",
            "site_basis": "\n".join(site_basis_lines),
            "applicability": "\n".join(applicability_lines),
            "capacity_comparison": "\n".join(capacity_lines),
            "why_primary": "\n".join("• " + r for r in recommendation_reasons),
            "warning": "\n".join("• " + w for w in warning_items),
            "soil_mix": f"Cohesive {cohesive_ratio*100:.0f}% / Frictional {frictional_ratio*100:.0f}%",
            "tip_soil": tip_soil,
        }

    def update_summary_panel(D, pile_length, analysis_depth, WT, FS, method, cohesive_model, loading_type, summary, qc_eb_text, layers=None, layer_lines=None):
        """
        Update modern summary cards on the right panel.
        Values are shown as engineering dashboard cards instead of one long text block.
        """
        def setv(key, value):
            if key in summary_vars:
                summary_vars[key].set(value)

        setv("pile_case", pile_case_combo.get())
        setv("method", method)
        setv("cohesive_model", cohesive_model)
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

        # Engineering Method Selection Advisor v4
        try:
            if layers is not None and layer_lines is not None:
                advisor = build_method_advisor_v4(
                    D=D,
                    analysis_depth=analysis_depth,
                    WT=WT,
                    FS=FS,
                    layers=layers,
                    layer_lines=layer_lines,
                    loading_type=loading_type,
                    cohesive_model=cohesive_model,
                )
                for k, v in advisor.items():
                    setv(f"advisor_{k}", v)
        except Exception as advisor_error:
            setv("advisor_primary_method", "Engineering review")
            setv("advisor_why_primary", f"Advisor could not be generated: {advisor_error}")

    def build_detailed_engineering_advisor(D, pile_length, analysis_depth, WT, FS, layers, layer_lines, loading_type, cohesive_model):
        """Build a detailed, rule-based and numerical engineering advisory report."""
        methods = ["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]
        sections = {}
        warnings = []
        critical = []

        # ---------- Geometry and profile checks ----------
        Di = D - 2.0 * WT
        ld_ratio = analysis_depth / D if D > 0 else 0.0
        geometry_lines = [
            f"Outside diameter, D = {D:.4f} m",
            f"Wall thickness, WT = {WT:.4f} m",
            f"Inside diameter, Di = {Di:.4f} m",
            f"Embedded length, L = {analysis_depth:.3f} m",
            f"Total pile length = {pile_length:.3f} m",
            f"L/D = {ld_ratio:.1f}",
            f"Factor of safety entered = {FS:.2f}",
        ]
        if D <= 0:
            critical.append("Pile diameter must be greater than zero.")
        if WT <= 0 or Di <= 0:
            critical.append("Wall thickness is invalid; D - 2WT must remain positive.")
        if analysis_depth > pile_length:
            warnings.append("Analysis depth exceeds total pile length.")
        if ld_ratio <= 10:
            warnings.append("L/D is not greater than 10; applicability of long flexible pile methods requires review.")
        else:
            geometry_lines.append("Long-pile geometry check: PASS (L/D > 10).")

        active=[]
        prev_to=None
        behavior_changes=0
        prev_beh=None
        cohesive_thk=frictional_thk=0.0
        missing=[]
        mixed=[]
        qcs=[]
        cus=[]
        tip_layer=None
        for i,ly in enumerate(layers, start=1):
            z1=max(0.0,float(ly.get('from_depth',0.0)))
            z2=min(analysis_depth,float(ly.get('to_depth',0.0)))
            if z2<=z1: continue
            active.append((i,ly,z1,z2))
            beh=str(ly.get('behavior','')).lower()
            soil=str(ly.get('soil_type','')).lower()
            if prev_to is not None:
                if z1 > prev_to + 1e-6: warnings.append(f"Gap in soil profile before Layer {i}: {prev_to:.2f}-{z1:.2f} m.")
                if z1 < prev_to - 1e-6: warnings.append(f"Overlap in soil profile at Layer {i} near {z1:.2f} m.")
            prev_to=z2
            if prev_beh is not None and beh != prev_beh: behavior_changes += 1
            prev_beh=beh
            thk=z2-z1
            if beh=='cohesive':
                cohesive_thk += thk
                if ly.get('cu') is None and ly.get('cu_top') is None: missing.append(f"Layer {i} cohesive: cu is missing.")
                for key in ('cu','cu_top','cu_bot'):
                    if ly.get(key) is not None:
                        try: cus.append(float(ly.get(key)))
                        except Exception: pass
            elif beh=='frictional':
                frictional_thk += thk
                if ly.get('qc_f') is None and ly.get('qc_f_top') is None: missing.append(f"Layer {i} frictional: qc_f is missing.")
                if ly.get('qc_eb') is None and ly.get('qc_eb_top') is None: missing.append(f"Layer {i} frictional: qc_eb is missing.")
                for key in ('qc_f','qc_f_top','qc_f_bot','qc_eb','qc_eb_top','qc_eb_bot'):
                    if ly.get(key) is not None:
                        try: qcs.append(float(ly.get(key))/1000.0)
                        except Exception: pass
            else:
                missing.append(f"Layer {i}: behavior must be cohesive or frictional.")
            if any(w in soil for w in ('silt','sand/clay','clay/sand','mixed','interbedded')):
                mixed.append(f"Layer {i} ({z1:.1f}-{z2:.1f} m, {ly.get('soil_type','')}): review as intermediate/mixed soil.")
            if z1 <= analysis_depth <= float(ly.get('to_depth',z2))+1e-9: tip_layer=ly
        total=max(cohesive_thk+frictional_thk,1e-9)
        cr=cohesive_thk/total; fr=frictional_thk/total
        profile_lines=[
            f"Active soil thickness assessed = {cohesive_thk+frictional_thk:.2f} m",
            f"Cohesive proportion = {cr*100:.1f}%",
            f"Frictional proportion = {fr*100:.1f}%",
            f"Behaviour transitions = {behavior_changes}",
            f"Profile interpretation = {'strongly interbedded/mixed' if behavior_changes >= 3 or (cr>0.25 and fr>0.25) else 'predominantly single behaviour'}",
            f"Pile-tip soil = {tip_layer.get('soil_type','Unknown') if tip_layer else 'Unknown'} ({tip_layer.get('behavior','Unknown') if tip_layer else 'Unknown'})",
        ]
        if qcs: profile_lines.append(f"Available frictional qc range = {min(qcs):.2f}-{max(qcs):.2f} MPa")
        if cus: profile_lines.append(f"Available clay cu range = {min(cus):.1f}-{max(cus):.1f} kPa")
        if missing: warnings.extend(missing)
        if mixed: warnings.extend(mixed)
        if active and active[-1][3] < analysis_depth-1e-6: critical.append("Soil profile does not extend to the analysis depth.")

        # ---------- Calculate all methods ----------
        method_data={}
        for m in methods:
            try:
                rows,summ,_=calculate_layer_capacity(D=D,L=analysis_depth,WT=WT,FS=FS,method=m,
                    layer_lines=layer_lines,loading_type=str(loading_type).lower(),cohesive_model=cohesive_model)
                qshaft=float(summ.get('Qshaft',0))/1000.0
                qbase=float(summ.get('Qbase',0))/1000.0
                qult=float(summ.get('Qult',0))/1000.0
                qallow=float(summ.get('Qallow',0))/1000.0
                method_data[m]={'rows':rows,'summary':summ,'Qshaft':qshaft,'Qbase':qbase,'Qult':qult,'Qallow':qallow}
            except Exception as e:
                method_data[m]={'error':str(e)}
        valid={m:d for m,d in method_data.items() if 'Qult' in d and d['Qult']>0}
        vals=[d['Qult'] for d in valid.values()]
        mean=sum(vals)/len(vals) if vals else 0
        spread=((max(vals)-min(vals))/mean*100) if mean else 0
        comparison=[]
        iso_ref=valid.get('ISO 19901-4:2025',{}).get('Qult')
        for m in methods:
            d=method_data[m]
            if 'error' in d:
                comparison.append(f"{m:<25} ERROR: {d['error']}")
                continue
            pct=((d['Qult']-iso_ref)/iso_ref*100) if iso_ref else None
            base_pct=(d['Qbase']/d['Qult']*100) if d['Qult'] else 0
            comparison.append(f"{m:<25} Qshaft={d['Qshaft']:8.2f} MN | Qbase={d['Qbase']:7.2f} MN | Qult={d['Qult']:8.2f} MN | Qallow={d['Qallow']:8.2f} MN | Base={base_pct:5.1f}%" + (f" | vs ISO={pct:+6.1f}%" if pct is not None else ""))
        comparison.append(f"Overall method spread = {spread:.1f}% of mean ultimate capacity.")
        if spread < 10: comparison.append("Interpretation: good agreement between methods.")
        elif spread < 20: comparison.append("Interpretation: moderate method sensitivity.")
        elif spread < 30: comparison.append("Interpretation: high method sensitivity; review governing layers and assumptions.")
        else: comparison.append("Interpretation: significant discrepancy; do not select a design value before detailed review.")

        # ---------- Method applicability ----------
        has_sand=fr>0.05; has_clay=cr>0.05
        app=[]
        app.append("ISO 19901-4:2025 Unified CPT Sand — RECOMMENDED as primary sand method" if has_sand and ld_ratio>10 else "ISO 19901-4:2025 Unified CPT Sand — CONDITIONAL / CHECK APPLICABILITY")
        app.append("ISO 19901-4:2025 Main Text Clay — RECOMMENDED where a representative cu profile is available" if has_clay and cus else "ISO 19901-4:2025 Main Text Clay — INSUFFICIENT cu DATA")
        app.append("ISO Unified CPT Clay (Annex) — NOT IMPLEMENTED / INSUFFICIENT INPUT: requires qt, sleeve friction fs, Fr, Qtn and CPT soil-behaviour classification.")
        app.append("Fugro-05 — PROJECT VERIFICATION method; valuable for comparison with the Fugro reference report.")
        app.append("UWA-05 — OPEN-ENDED/PLUGGING sensitivity method.")
        app.append("ICP-05 — SHAFT-MECHANISM/friction-fatigue comparison method.")
        app.append("NGI-05 — DEEP-LAYER independent sensitivity method.")
        app.append("API RP 2A (1979-1986) / Annex C — LEGACY clay comparison, not automatic primary basis for new design.")
        app.append("API Main Text — BASELINE and transparent manual-check method.")

        # ---------- Contribution ranking for selected method ----------
        selected=method_data.get(method_combo.get(),{})
        contributions=[]
        if selected.get('rows'):
            ranked=[]
            for r in selected['rows']:
                try: ranked.append((float(r.get('qshaft_layer',0))/1000.0, r.get('depth_range',''), r.get('soil_type',''), r.get('behavior','')))
                except Exception: pass
            ranked.sort(reverse=True,key=lambda x:x[0])
            total_shaft=sum(max(0,x[0]) for x in ranked)
            for idx,(q,z,soil,beh) in enumerate(ranked[:8],start=1):
                pct=q/total_shaft*100 if total_shaft else 0
                contributions.append(f"{idx}. {z} m | {soil} ({beh}) | layer shaft contribution = {q:.2f} MN ({pct:.1f}% of shaft)")
            if ranked and total_shaft and ranked[0][0]/total_shaft > 0.25:
                warnings.append(f"One layer contributes more than 25% of selected-method shaft capacity; verify parameters in {ranked[0][1]} m.")
        if selected.get('Qult'):
            base_ratio=selected['Qbase']/selected['Qult']*100
            contributions.append(f"Selected method base contribution = {base_ratio:.1f}% of Qult.")
            if base_ratio>35: warnings.append("Base resistance exceeds 35% of Qult; result is sensitive to pile-tip qc averaging, tip classification and plugging assumptions.")
            elif base_ratio<15: contributions.append("Pile behaviour is predominantly shaft-controlled.")

        # ---------- Recommendation ----------
        recommendation=[]
        if has_sand:
            recommendation.append("Use ISO 19901-4:2025 Unified CPT as the primary calculation basis for applicable frictional layers in new design.")
        if has_clay:
            recommendation.append("Use ISO 19901-4:2025 Main Text alpha-method for cohesive layers with the current cu-based input profile.")
        recommendation.append("Retain Fugro-05 as the principal project-verification comparison against the WPA reference report.")
        recommendation.append("Use ICP-05, UWA-05 and NGI-05 as method-sensitivity checks; do not average methods unless the project design basis explicitly permits it.")
        recommendation.append("Use API RP 2A (1979-1986) only for legacy comparison, reassessment, or when specified by the project.")
        recommendation.append("Do not select the method producing the highest capacity automatically. The governing method must also be applicable to soil type, pile geometry, installation method and data quality.")
        recommendation.append("ISO 2025 is a partial-factor design framework. FS-based allowable capacity shown by this program is a comparison output unless project-specific resistance factors and action combinations are applied.")

        sections['EXECUTIVE RECOMMENDATION']='\n'.join('• '+x for x in recommendation)
        sections['PILE GEOMETRY AND DESIGN BASIS']='\n'.join(geometry_lines)
        sections['SOIL PROFILE ASSESSMENT']='\n'.join(profile_lines)
        sections['METHOD APPLICABILITY MATRIX']='\n'.join('• '+x for x in app)
        sections['NUMERICAL METHOD COMPARISON']='\n'.join(comparison)
        sections['LAYER AND SHAFT/BASE CONTRIBUTION']='\n'.join(contributions) if contributions else 'No contribution data available.'
        sections['WARNINGS AND LIMITATIONS']='\n'.join(('CRITICAL: '+x for x in critical)) + ('\n' if critical and warnings else '') + '\n'.join('WARNING: '+x for x in warnings)
        if not critical and not warnings: sections['WARNINGS AND LIMITATIONS']='No automatic critical issues detected. Engineering review is still required.'
        sections['FINAL ADVISOR STATEMENT']=(
            "The recommendation is an engineering decision-support output, not an automatic design approval. "
            "Final selection shall be confirmed against project specifications, representative soil parameters, installation records, "
            "pile load-test evidence where available, and the applicable resistance-factor format."
        )
        return sections

    def show_detailed_engineering_advisor():
        try:
            D=float(entry_diameter.get()); pile_length=float(entry_length.get()); analysis_depth=float(entry_analysis_depth.get())
            WT=float(entry_wt.get()); FS=float(entry_fs.get())
            loading_type=loading_combo.get().lower(); cohesive_model=cohesive_combo.get()
            layer_lines=layer_text.get('1.0',tk.END).strip().split('\n')
            layers=parse_layer_lines(layer_lines)
            sections=build_detailed_engineering_advisor(D,pile_length,analysis_depth,WT,FS,layers,layer_lines,loading_type,cohesive_model)

            win=tk.Toplevel(root)
            win.title('Engineering Advisor — Detailed Method Selection and Design Review')
            win.geometry('1120x780')
            win.minsize(850,600)
            win.configure(bg='#EAF1F8')
            header=tk.Frame(win,bg='#003B71',height=72)
            header.pack(fill='x'); header.pack_propagate(False)
            tk.Label(header,text='ENGINEERING ADVISOR',bg='#003B71',fg='white',font=('Segoe UI',18,'bold')).pack(anchor='w',padx=20,pady=(12,0))
            tk.Label(header,text='Method applicability • numerical comparison • layer contribution • warnings',bg='#003B71',fg='#D8E8F7',font=('Segoe UI',9)).pack(anchor='w',padx=20)
            nb=ttk.Notebook(win)
            nb.pack(fill='both',expand=True,padx=14,pady=14)
            groups=[
                ('Recommendation',['EXECUTIVE RECOMMENDATION','FINAL ADVISOR STATEMENT']),
                ('Applicability',['PILE GEOMETRY AND DESIGN BASIS','SOIL PROFILE ASSESSMENT','METHOD APPLICABILITY MATRIX']),
                ('Comparison',['NUMERICAL METHOD COMPARISON']),
                ('Contributions',['LAYER AND SHAFT/BASE CONTRIBUTION']),
                ('Warnings',['WARNINGS AND LIMITATIONS']),
                ('Full Report',list(sections.keys())),
            ]
            for tab_name,keys in groups:
                frame=tk.Frame(nb,bg='white'); nb.add(frame,text=tab_name)
                txt=tk.Text(frame,wrap='word',font=('Menlo',10),bg='white',fg='#172033',relief='flat',padx=18,pady=18)
                sb=ttk.Scrollbar(frame,orient='vertical',command=txt.yview); txt.configure(yscrollcommand=sb.set)
                sb.pack(side='right',fill='y'); txt.pack(side='left',fill='both',expand=True)
                for key in keys:
                    txt.insert('end',key+'\n'+'='*len(key)+'\n'+sections[key]+'\n\n')
                txt.configure(state='disabled')
            footer=tk.Frame(win,bg='#EAF1F8'); footer.pack(fill='x',padx=14,pady=(0,12))
            def copy_full():
                report='\n\n'.join(k+'\n'+'='*len(k)+'\n'+v for k,v in sections.items())
                win.clipboard_clear(); win.clipboard_append(report); messagebox.showinfo('Engineering Advisor','Full advisor report copied to clipboard.')
            ttk.Button(footer,text='Copy Full Advisor Report',command=copy_full,style='Primary.TButton').pack(side='right')
        except Exception as e:
            messagebox.showerror('Engineering Advisor',f'Cannot generate advisor report.\n\n{e}')

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

    def make_all_methods_curve_figure(loading_type, cohesive_model_override=None, selected_methods=None, include_average=True):
        D = float(entry_diameter.get())
        WT = float(entry_wt.get())
        FS = float(entry_fs.get())
        analysis_depth = float(entry_analysis_depth.get())
        cohesive_model = cohesive_model_override if cohesive_model_override is not None else cohesive_combo.get()
        layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
        layers = parse_layer_lines(layer_lines)

        # Dynamic depth limit for long example profiles.
        max_depth = max(layer["to_depth"] for layer in layers)
        max_depth = int(math.ceil(max_depth / 20.0) * 20)

        plt.rcParams["font.family"] = REPORT_FONT
        plt.rcParams["font.sans-serif"] = REPORT_FONT_FAMILY
        plt.rcParams["axes.linewidth"] = 0.8

        methods = [
            ("API Main Text", "API RP 2GEO (October 2014) - Main Text Method", "orange", "-"),
            ("API RP 2A (1979-1986)", "Traditional API RP 2A (1979-1986), K=0.8/0.5", "blue", ":"),
            ("ISO 19901-4:2025", "ISO 19901-4:2025 - Unified CPT Method", "black", "-"),
            ("ICP-05", "API RP 2GEO (October 2014) - Method 1, Simplified ICP-05", "green", "--"),
            ("UWA-05", "API RP 2GEO (October 2014) - Method 2, Offshore UWA-05", "magenta", "-"),
            ("Fugro-05", "API RP 2GEO (October 2014) - Method 3, Fugro-05", "cyan", "-."),
            ("NGI-05", "API RP 2GEO (October 2014) - Method 4, NGI-05", "red", "--")
        ]

        # Keep only the methods selected by the user. Calls from PDF/report export
        # omit selected_methods and therefore retain the complete comparison.
        if selected_methods is not None:
            selected_set = set(selected_methods)
            methods = [item for item in methods if item[0] in selected_set]

        if not methods:
            raise ValueError("Please select at least one comparison method.")

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
        average_curves = []
        average_depths = None

        for method, label, color, linestyle in methods:
            depths, qult, _ = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
                cohesive_model=cohesive_model
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

                # Store curves for the average capacity trend line.
                # All implemented methods are evaluated at the same analysis depths.
                if average_depths is None:
                    average_depths = list(plot_depths)
                average_curves.append(list(plot_qult))

        # Add Average curve: arithmetic mean of all plotted method capacities
        # at each analysis depth. This is for trend comparison only.
        if include_average and average_curves and average_depths:
            average_curve = [
                sum(values) / len(values)
                for values in zip(*average_curves)
            ]
            all_capacity_values.extend(average_curve)
            ax.plot(
                average_curve,
                average_depths,
                color="black",
                linestyle="--",
                linewidth=2.8,
                label="Average"
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

        if cohesive_model == "API RP 2GEO (October 2014) - Annex C":
            cohesive_note = "API RP 2GEO (October 2014) - Annex C (former API RP 2A - 1979)"
        else:
            cohesive_note = "API RP 2GEO (October 2014)"

        friction_note_map = {
            "API Main Text": "API RP 2GEO (October 2014) Main Text",
            "API RP 2A (1979-1986)": "Traditional API RP 2A (1979-1986)",
            "ISO 19901-4:2025": "ISO 19901-4:2025 Unified CPT",
            "ICP-05": "API RP 2GEO Method 1, Simplified ICP-05",
            "UWA-05": "API RP 2GEO Method 2, Offshore UWA-05",
            "Fugro-05": "API RP 2GEO Method 3, Fugro-05",
            "NGI-05": "API RP 2GEO Method 4, NGI-05",
        }
        selected_friction_names = [item[0] for item in methods]
        friction_note = ", ".join(
            friction_note_map.get(name, name) for name in selected_friction_names
        )

        notes_text = (
            "Notes:\n"
            f"1. Cohesive Model: {cohesive_note}\n"
            f"2. Frictional Model(s): {friction_note}"
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
            "CPT-CALC-RPT-001 | Interactive Axial Pile Calculation Report for WPA-01 Platform Site",
            ha="left",
            fontsize=5.8
        )

        plate_no = "Figure CAP-XX"
        if pile_case_combo.get() == "54-in OD" and loading_type == "compression":
            plate_no = "Figure CAP-C-01"
        elif pile_case_combo.get() == "66-in OD" and loading_type == "compression":
            plate_no = "Figure CAP-C-02"
        elif loading_type == "tension":
            plate_no = "Figure CAP-T-01"
        fig.text(0.10, 0.026, plate_no, ha="left", fontsize=5.8)

        return fig

    def make_single_method_compression_tension_figure(method, cohesive_model_override=None):
        """Create one Fugro-style page containing compression and tension curves for one friction method."""
        D = float(entry_diameter.get())
        WT = float(entry_wt.get())
        FS = float(entry_fs.get())
        analysis_depth = float(entry_analysis_depth.get())
        cohesive_model = cohesive_model_override if cohesive_model_override is not None else cohesive_combo.get()
        layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
        layers = parse_layer_lines(layer_lines)

        max_depth = max(layer["to_depth"] for layer in layers)
        max_depth = int(math.ceil(max_depth / 20.0) * 20)

        method_label_map = {
            "API Main Text": "API RP 2GEO (October 2014) - Main Text Method",
            "API RP 2A (1979-1986)": "Traditional API RP 2A (1979-1986), K=0.8/0.5",
            "ISO 19901-4:2025": "ISO 19901-4:2025 - Unified CPT Method",
            "ICP-05": "API RP 2GEO (October 2014) - Method 1, Simplified ICP-05",
            "UWA-05": "API RP 2GEO (October 2014) - Method 2, Offshore UWA-05",
            "Fugro-05": "API RP 2GEO (October 2014) - Method 3, Fugro-05",
            "NGI-05": "API RP 2GEO (October 2014) - Method 4, NGI-05",
        }
        method_label = method_label_map.get(method, method)

        plt.rcParams["font.family"] = REPORT_FONT
        plt.rcParams["font.sans-serif"] = REPORT_FONT_FAMILY
        plt.rcParams["axes.linewidth"] = 0.8

        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        ax = fig.add_axes([0.11, 0.25, 0.63, 0.60])
        ax_soil = fig.add_axes([0.78, 0.25, 0.14, 0.60], sharey=ax)

        all_values = []
        curve_specs = [
            ("compression", "Compression", "black", "-", 1.25),
            ("tension", "Tension", "limegreen", "--", 1.15),
        ]

        for loading_type, label, color, linestyle, linewidth in curve_specs:
            depths, qult, _ = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
                cohesive_model=cohesive_model
            )
            plot_depths, plot_qult = [], []
            for d, q in zip(depths, qult):
                if d <= analysis_depth:
                    plot_depths.append(d)
                    plot_qult.append(q)
                    all_values.append(q)
            if plot_depths:
                ax.plot(plot_qult, plot_depths, color=color, linestyle=linestyle,
                        linewidth=linewidth, label=label)

        if all_values:
            x_max_raw = max(all_values)
            if x_max_raw <= 60:
                x_max, step = 60, 10
            elif x_max_raw <= 120:
                x_max, step = 120, 10
            else:
                x_max = int(math.ceil(x_max_raw / 50.0) * 50)
                step = 50
        else:
            x_max, step = 60, 10

        ax.set_xlim(0, x_max)
        ax.set_ylim(max_depth, 0)
        ax.set_xticks(range(0, int(x_max) + 1, step))
        ax.set_yticks(range(0, int(max_depth) + 1, 20))
        ax.set_yticks(range(0, int(max_depth) + 1, 10), minor=True)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xlabel("Ultimate Axial Pile Capacity [MN]", fontsize=7)
        ax.set_ylabel("Depth Below Seafloor [m]", fontsize=7)
        ax.tick_params(axis="both", labelsize=6.5)
        ax.grid(True, which="major", color="black", linewidth=0.50)
        ax.grid(True, which="minor", color="black", linewidth=0.22, alpha=0.45)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

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
                hatch, code = "", "C"
            elif behavior == "frictional":
                hatch, code = "///", "F"
            else:
                hatch, code = "...", "R"
            ax_soil.fill_betweenx([z1, z2], 0.00, 0.42, facecolor="white",
                                  edgecolor="black", hatch=hatch, linewidth=0.55)
            mid = 0.5 * (z1 + z2)
            thickness = z2 - z1
            code_fs = 4.8 if thickness < 1.5 else (5.4 if thickness < 3.0 else 6.2)
            soil_fs = None if thickness < 1.5 else (4.5 if thickness < 3.0 else (5.4 if len(soil) <= 8 else 4.8))
            ax_soil.text(0.21, mid, code, ha="center", va="center", fontsize=code_fs, fontweight="bold")
            if soil_fs is not None:
                ax_soil.text(0.72, mid, soil, ha="center", va="center", fontsize=soil_fs)
        ax_soil.set_title("Ground\nBehaviour\n/\nGround\nUnit\nName", fontsize=6.0, pad=8)
        for spine in ax_soil.spines.values():
            spine.set_linewidth(0.8)

        fig.text(0.50, 0.940, "ULTIMATE AXIAL PILE CAPACITY", ha="center", fontsize=8.2, fontweight="bold")
        fig.text(0.50, 0.920, f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}", ha="center", fontsize=6.2)
        fig.text(0.82, 0.963, "PTTEP International Limited", ha="center", fontsize=5.6)

        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.10, 0.188),
                   fontsize=7.0, frameon=False, ncol=1, handlelength=3.2,
                   handletextpad=0.8, labelspacing=0.30, borderaxespad=0.0)

        if cohesive_model == "API RP 2GEO (October 2014) - Annex C":
            cohesive_note = "API RP 2GEO (October 2014) - Annex C (former API RP 2A - 1979)"
        else:
            cohesive_note = "API RP 2GEO (October 2014)"

        notes_text = (
            "Notes:\n"
            f"1. Cohesive Model: {cohesive_note}\n"
            f"2. Frictional Model: {method_label}"
        )
        fig.text(0.10, 0.150, notes_text, fontsize=6.5, ha="left", va="top", linespacing=1.22)

        fig.text(0.50, 0.085, "ULTIMATE AXIAL PILE CAPACITY", ha="center", fontsize=8.2, fontweight="bold")
        fig.text(0.50, 0.067, f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}", ha="center", fontsize=6.5)
        fig.text(0.10, 0.038,
                 "CPT-CALC-RPT-001 | Interactive Axial Pile Calculation Report for WPA-01 Platform Site",
                 ha="left", fontsize=5.8)
        fig.text(0.10, 0.026, "Figure CAP-CT-01", ha="left", fontsize=5.8)
        return fig

    def make_unit_profile_figure(profile_type="shaft", loading_type="compression", cohesive_model_override=None, selected_methods=None, selected_clay_models=None):
        """
        Fugro-style unit resistance profile with separated soil-model families.

        Requested display logic:
        - Clay is shown as 2 cohesive-model curves:
            1) API RP 2GEO (October 2014) Main Text
            2) API RP 2GEO (October 2014) - Annex C
        - Sand / frictional layers are shown as 5 frictional-method curves:
            1) API Main Text
            2) API RP 2A (1979-1986)
            3) ICP-05
            4) UWA-05
            5) Fugro-05
            6) NGI-05

        This avoids making two separate pages for Main Text vs Annex C when the only real
        difference is the clay shaft-friction model. Frictional layers remain method-based.
        """
        D = float(entry_diameter.get())
        WT = float(entry_wt.get())
        FS = float(entry_fs.get())
        analysis_depth = float(entry_analysis_depth.get())
        layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
        layers = parse_layer_lines(layer_lines)

        max_depth = max(layer["to_depth"] for layer in layers)
        max_depth = int(math.ceil(max_depth / 20.0) * 20)

        plt.rcParams["font.family"] = REPORT_FONT
        plt.rcParams["font.sans-serif"] = REPORT_FONT_FAMILY
        plt.rcParams["axes.linewidth"] = 0.8

        all_clay_models = [
            ("API RP 2GEO (October 2014)", "clay_main", "Clay - API RP 2GEO Main Text", "blue", "-"),
            ("API RP 2GEO (October 2014) - Annex C", "clay_annex", "Clay - API RP 2GEO Annex C", "blue", "--"),
        ]
        selected_clay_set = set(selected_clay_models or [item[0] for item in all_clay_models])
        clay_models = [item[1:] for item in all_clay_models if item[0] in selected_clay_set]

        all_sand_methods = [
            ("API Main Text", "Sand - API Main Text", "orange", "-"),
            ("API RP 2A (1979-1986)", "Sand/Silt - API RP 2A (1979-1986)", "blue", ":"),
            ("ISO 19901-4:2025", "Sand - ISO 19901-4:2025 Unified CPT", "black", "-"),
            ("ICP-05", "Sand - Method 1, ICP-05", "green", "-"),
            ("UWA-05", "Sand - Method 2, UWA-05", "magenta", "--"),
            ("Fugro-05", "Sand - Method 3, Fugro-05", "cyan", "-."),
            ("NGI-05", "Sand - Method 4, NGI-05", "red", ":"),
        ]
        selected_method_set = set(selected_methods or [item[0] for item in all_sand_methods])
        sand_methods = [item for item in all_sand_methods if item[0] in selected_method_set]

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
                    linewidth=0.55,
                )

                mid = 0.5 * (z1 + z2)
                thickness = z2 - z1
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

        def unit_shaft_clay_main(layer, z):
            cu = layer_value(layer, "cu", z)
            if cu is None:
                return 0.0
            p0 = effective_stress_at_depth(layers, z)
            psi = cu / p0
            if psi <= 1.0:
                alpha = 0.5 * psi ** (-0.5)
            else:
                alpha = 0.5 * psi ** (-0.25)
            alpha = min(alpha, 1.0)
            value = alpha * cu
            if layer.get("flim") is not None:
                value = min(value, layer["flim"])
            return value

        def unit_shaft_clay_annex(layer, z):
            cu = layer_value(layer, "cu", z)
            if cu is None:
                return 0.0
            if cu <= 24.0:
                alpha = 1.0
            elif cu >= 72.0:
                alpha = 0.5
            else:
                alpha = 1.0 - (cu - 24.0) / 96.0
            value = alpha * cu
            if layer.get("flim") is not None:
                value = min(value, layer["flim"])
            return value

        def add_step_segment(xs, ys, value, z1, z2):
            if xs:
                xs.append(float("nan"))
                ys.append(float("nan"))
            xs.extend([value, value])
            ys.extend([z1, z2])

        def build_unit_shaft_curve(curve_type, method_name=None):
            xs, ys, vals = [], [], []
            loading_for_calc = str(loading_type or "compression").lower()

            # IMPORTANT:
            # The layer table reports average unit shaft resistance from
            # integrate_layer_shaft().  The graph must use the same averaged
            # value, not the midpoint value, otherwise the plotted step can
            # differ from the table when cu, qc, or effective stress varies
            # within a layer.
            for layer in layers:
                z1 = layer["from_depth"]
                z2 = min(layer["to_depth"], analysis_depth)
                if z2 <= z1:
                    continue

                if curve_type == "clay_main":
                    if layer["behavior"] != "cohesive":
                        continue
                    value, _, _ = integrate_layer_shaft(
                        layer,
                        D,
                        analysis_depth,
                        WT,
                        layers,
                        method_name or "API Main Text",
                        loading_for_calc,
                        "API RP 2GEO (October 2014)",
                    )
                elif curve_type == "clay_annex":
                    if layer["behavior"] != "cohesive":
                        continue
                    value, _, _ = integrate_layer_shaft(
                        layer,
                        D,
                        analysis_depth,
                        WT,
                        layers,
                        method_name or "API Main Text",
                        loading_for_calc,
                        "API RP 2GEO (October 2014) - Annex C",
                    )
                else:
                    if layer["behavior"] != "frictional":
                        continue
                    value, _, _ = integrate_layer_shaft(
                        layer,
                        D,
                        analysis_depth,
                        WT,
                        layers,
                        method_name,
                        loading_for_calc,
                        cohesive_model_override or cohesive_combo.get(),
                    )

                add_step_segment(xs, ys, value, z1, z2)
                vals.append(value)
            return xs, ys, vals

        def build_unit_base_curve(curve_type, method_name=None):
            xs, ys, vals = [], [], []
            for layer in layers:
                z1 = layer["from_depth"]
                z2 = min(layer["to_depth"], analysis_depth)
                if z2 <= z1:
                    continue
                z_mid = 0.5 * (z1 + z2)

                if curve_type in ["clay_main", "clay_annex"]:
                    if layer["behavior"] != "cohesive":
                        continue
                    # API Main Text and Annex C use the same clay end-bearing expression here.
                    # The Annex-C difference in this program is the shaft-friction alpha model.
                    value = end_bearing_cohesive(layer, z_mid) / 1000.0  # kPa -> MPa
                else:
                    if layer["behavior"] != "frictional":
                        continue
                    try:
                        _rows, summary, _ = calculate_layer_capacity(
                            D=D,
                            L=z_mid,
                            WT=WT,
                            FS=FS,
                            method=method_name,
                            layer_lines=layer_lines,
                            loading_type="compression",
                            cohesive_model="API RP 2GEO (October 2014)",
                        )
                        value = float(summary.get("q_unit_base", 0.0)) / 1000.0  # kPa -> MPa
                    except Exception:
                        value = 0.0

                add_step_segment(xs, ys, value, z1, z2)
                vals.append(value)
            return xs, ys, vals

        profile_type = str(profile_type).lower()
        if profile_type == "end_bearing":
            title = "UNIT END BEARING PROFILE"
            xlabel = "Unit End Bearing, qbase [MPa]"
            note_specific = "Clay is shown as Main Text and Annex C; frictional layers are shown by API Main Text, ISO 19901-4:2025 and CPT-based methods."
        else:
            loading_for_calc = str(loading_type or "compression").lower()
            load_word = "Compression" if loading_for_calc == "compression" else "Tension"
            title = f"UNIT SHAFT FRICTION PROFILE IN {load_word.upper()}"
            xlabel = f"Unit Shaft Friction, f(z) in {load_word} [kPa]"
            note_specific = "Clay uses two cohesive models; sand uses API Main Text, ISO 19901-4:2025 and four CPT-based methods."

        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        ax = fig.add_axes([0.11, 0.27, 0.63, 0.58])
        ax_soil = fig.add_axes([0.78, 0.27, 0.14, 0.58], sharey=ax)

        all_values = []

        # Clay curves first
        for curve_type, label, color, linestyle in clay_models:
            try:
                if profile_type == "end_bearing":
                    plot_values, plot_depths, values = build_unit_base_curve(curve_type)
                else:
                    plot_values, plot_depths, values = build_unit_shaft_curve(curve_type)
                all_values.extend(values)
                if plot_depths:
                    ax.plot(plot_values, plot_depths, color=color, linestyle=linestyle, linewidth=1.10, label=label)
            except Exception:
                continue

        # Frictional / sand curves
        for method, label, color, linestyle in sand_methods:
            try:
                if profile_type == "end_bearing":
                    plot_values, plot_depths, values = build_unit_base_curve("sand", method_name=method)
                else:
                    plot_values, plot_depths, values = build_unit_shaft_curve("sand", method_name=method)
                all_values.extend(values)
                if plot_depths:
                    ax.plot(plot_values, plot_depths, color=color, linestyle=linestyle, linewidth=1.05, label=label)
            except Exception:
                continue

        if all_values:
            x_max = max(all_values)
            if profile_type == "end_bearing":
                if x_max <= 20:
                    x_tick_step = 2
                elif x_max <= 60:
                    x_tick_step = 5
                else:
                    x_tick_step = 10
                x_max = max(x_tick_step, int(math.ceil(x_max / x_tick_step) * x_tick_step))
            else:
                if x_max <= 250:
                    x_tick_step = 25
                elif x_max <= 500:
                    x_tick_step = 50
                else:
                    x_tick_step = 100
                x_max = max(x_tick_step, int(math.ceil(x_max / x_tick_step) * x_tick_step))
        else:
            x_max = 100
            x_tick_step = 25

        ax.set_xlim(0, x_max)
        ax.set_ylim(max_depth, 0)
        ax.set_xticks([x for x in range(0, int(x_max) + 1, int(x_tick_step))])
        ax.set_yticks(range(0, int(max_depth) + 1, 20))
        ax.set_yticks(range(0, int(max_depth) + 1, 10), minor=True)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xlabel(xlabel, fontsize=7)
        ax.set_ylabel("Depth Below Seafloor [m]", fontsize=7)
        ax.tick_params(axis="both", labelsize=6.5)
        ax.grid(True, which="major", color="black", linewidth=0.50)
        ax.grid(True, which="minor", color="black", linewidth=0.22, alpha=0.45)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

        draw_soil_column(ax_soil, layers, max_depth)

        fig.text(0.50, 0.940, title, ha="center", fontsize=8.2, fontweight="bold")
        fig.text(0.50, 0.920, f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}", ha="center", fontsize=6.2)
        fig.text(0.82, 0.963, "PTTEP International Limited", ha="center", fontsize=5.6)

        handles, labels = ax.get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower left",
            bbox_to_anchor=(0.10, 0.174),
            fontsize=6.6,
            frameon=False,
            ncol=1,
            handlelength=3.2,
            handletextpad=0.8,
            labelspacing=0.25,
            borderaxespad=0.0,
        )

        clay_note_map = {
            "API RP 2GEO (October 2014)": "API RP 2GEO Main Text",
            "API RP 2GEO (October 2014) - Annex C": "API RP 2GEO Annex C (former API RP 2A-1979)",
        }
        sand_note_map = {
            "API Main Text": "API Main Text",
            "API RP 2A (1979-1986)": "Traditional API RP 2A (1979-1986)",
            "ISO 19901-4:2025": "ISO 19901-4:2025 Unified CPT",
            "ICP-05": "ICP-05",
            "UWA-05": "UWA-05",
            "Fugro-05": "Fugro-05",
            "NGI-05": "NGI-05",
        }
        clay_note = ", ".join(
            clay_note_map.get(name, name)
            for name in (selected_clay_models or [item[0] for item in all_clay_models])
            if name in selected_clay_set
        ) or "None selected"
        sand_note = ", ".join(
            sand_note_map.get(name, name)
            for name in (selected_methods or [item[0] for item in all_sand_methods])
            if name in selected_method_set
        ) or "None selected"

        notes_text = (
            "Notes:\n"
            f"1. {note_specific}\n"
            f"2. Clay curve(s): {clay_note}.\n"
            f"3. Frictional curve(s): {sand_note}.\n"
            "4. Curves are generated from layer-by-layer unit resistance values."
        )
        fig.text(0.10, 0.145, notes_text, fontsize=6.5, ha="left", va="top", linespacing=1.22)

        fig.text(0.50, 0.085, title, ha="center", fontsize=8.2, fontweight="bold")
        fig.text(0.50, 0.067, f"DRIVEN OPEN-ENDED CIRCULAR PILE - {pile_case_combo.get()}", ha="center", fontsize=6.5)
        fig.text(0.10, 0.038, "CPT-CALC-RPT-001 | Interactive Axial Pile Calculation Report for WPA-01 Platform Site", ha="left", fontsize=5.8)
        fig.text(0.10, 0.026, "Unit Resistance Figure", ha="left", fontsize=5.8)

        return fig

    def show_unit_profile_selector(profile_type):
        method_options = [
            ("API Main Text", "API RP 2GEO Main Text"),
            ("API RP 2A (1979-1986)", "Traditional API RP 2A (1979–1986)"),
            ("ISO 19901-4:2025", "ISO 19901-4:2025 Unified CPT"),
            ("ICP-05", "Simplified ICP-05"),
            ("UWA-05", "Offshore UWA-05"),
            ("Fugro-05", "Fugro-05"),
            ("NGI-05", "NGI-05"),
        ]
        clay_options = [
            ("API RP 2GEO (October 2014)", "API RP 2GEO Main Text clay model"),
            ("API RP 2GEO (October 2014) - Annex C", "API RP 2GEO Annex C / former API RP 2A-1979 clay model"),
        ]

        dialog = tk.Toplevel(root)
        title_name = "Unit Shaft Friction" if profile_type == "shaft" else "Unit End Bearing"
        dialog.title(f"Select Methods for {title_name}")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"Select methods for {title_name} profile",
            bg="white",
            fg="#003B71",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(
            dialog,
            text="Tick only the frictional methods and clay models you want to display.",
            bg="white",
            fg="#64748B",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=18, pady=(0, 10))

        tk.Label(
            dialog,
            text="Frictional methods",
            bg="white",
            fg="#003B71",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=18, pady=(0, 4))

        vars_by_method = {}
        methods_frame = tk.Frame(dialog, bg="white")
        methods_frame.pack(fill="both", expand=True, padx=18)
        for method_key, display_name in method_options:
            var = tk.BooleanVar(value=True)
            vars_by_method[method_key] = var
            ttk.Checkbutton(methods_frame, text=display_name, variable=var).pack(anchor="w", pady=2)

        ttk.Separator(dialog, orient="horizontal").pack(fill="x", padx=18, pady=(10, 8))
        tk.Label(
            dialog,
            text="Cohesive-soil models",
            bg="white",
            fg="#003B71",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=18, pady=(0, 4))

        vars_by_clay = {}
        clay_frame = tk.Frame(dialog, bg="white")
        clay_frame.pack(fill="x", padx=18, pady=(0, 6))
        for clay_key, display_name in clay_options:
            default_selected = clay_key == cohesive_combo.get()
            var = tk.BooleanVar(value=default_selected)
            vars_by_clay[clay_key] = var
            ttk.Checkbutton(clay_frame, text=display_name, variable=var).pack(anchor="w", pady=2)

        def set_all(value):
            for var in vars_by_method.values():
                var.set(value)
            for var in vars_by_clay.values():
                var.set(value)

        quick_frame = tk.Frame(dialog, bg="white")
        quick_frame.pack(fill="x", padx=18, pady=(6, 8))
        ttk.Button(quick_frame, text="Select All", command=lambda: set_all(True)).pack(side="left", padx=(0, 6))
        ttk.Button(quick_frame, text="Clear All", command=lambda: set_all(False)).pack(side="left")
        ttk.Button(
            quick_frame,
            text="Modern Methods",
            command=lambda: [
                var.set(key in {"ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"})
                for key, var in vars_by_method.items()
            ],
        ).pack(side="left", padx=(6, 0))

        def generate_selected_profile():
            selected_methods = [key for key, var in vars_by_method.items() if var.get()]
            selected_clay_models = [key for key, var in vars_by_clay.items() if var.get()]
            if not selected_methods and not selected_clay_models:
                messagebox.showwarning(
                    "Select Method",
                    "Please select at least one frictional method or cohesive-soil model.",
                    parent=dialog,
                )
                return
            dialog.destroy()
            try:
                fig = make_unit_profile_figure(
                    profile_type,
                    loading_type=loading_combo.get().lower() if profile_type == "shaft" else "compression",
                    selected_methods=selected_methods,
                    selected_clay_models=selected_clay_models,
                )
                plt.show()
            except Exception as e:
                messagebox.showerror("Error", f"สร้าง {title_name} Profile ไม่ได้\n\n{e}")

        action_frame = tk.Frame(dialog, bg="white")
        action_frame.pack(fill="x", padx=18, pady=(4, 16))
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(
            action_frame,
            text="Generate Graph",
            style="Primary.TButton",
            command=generate_selected_profile,
        ).pack(side="right", padx=(0, 8))

        dialog.update_idletasks()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - dialog.winfo_width()) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")

    def show_unit_friction_profile():
        show_unit_profile_selector("shaft")

    def show_unit_end_bearing_profile():
        show_unit_profile_selector("end_bearing")

    def show_all_methods_curve(loading_type):
        method_options = [
            ("API Main Text", "API RP 2GEO Main Text"),
            ("API RP 2A (1979-1986)", "Traditional API RP 2A (1979–1986)"),
            ("ISO 19901-4:2025", "ISO 19901-4:2025 Unified CPT"),
            ("ICP-05", "Simplified ICP-05"),
            ("UWA-05", "Offshore UWA-05"),
            ("Fugro-05", "Fugro-05"),
            ("NGI-05", "NGI-05"),
        ]

        dialog = tk.Toplevel(root)
        dialog.title("Select Methods for Comparison")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"Select methods for {loading_type.title()} graph",
            bg="white",
            fg="#003B71",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 4))

        tk.Label(
            dialog,
            text="Tick only the methods you want to display.",
            bg="white",
            fg="#64748B",
            font=("Segoe UI", 8)
        ).pack(anchor="w", padx=18, pady=(0, 10))

        vars_by_method = {}
        options_frame = tk.Frame(dialog, bg="white")
        options_frame.pack(fill="both", expand=True, padx=18)

        for method_key, display_name in method_options:
            var = tk.BooleanVar(value=True)
            vars_by_method[method_key] = var
            ttk.Checkbutton(
                options_frame,
                text=display_name,
                variable=var
            ).pack(anchor="w", pady=3)

        # Cohesive-soil model used for every selected comparison method.
        # This is intentionally selected inside the graph dialog so the user can
        # generate different comparison plots without changing the main input panel.
        ttk.Separator(dialog, orient="horizontal").pack(fill="x", padx=18, pady=(10, 8))
        tk.Label(
            dialog,
            text="Select cohesive-soil model",
            bg="white",
            fg="#003B71",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 4))

        cohesive_model_var = tk.StringVar(value=cohesive_combo.get())
        cohesive_options_frame = tk.Frame(dialog, bg="white")
        cohesive_options_frame.pack(fill="x", padx=18, pady=(0, 6))

        ttk.Radiobutton(
            cohesive_options_frame,
            text="API RP 2GEO Main Text clay model",
            variable=cohesive_model_var,
            value="API RP 2GEO (October 2014)"
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            cohesive_options_frame,
            text="API RP 2GEO Annex C / former API RP 2A-1979 clay model",
            variable=cohesive_model_var,
            value="API RP 2GEO (October 2014) - Annex C"
        ).pack(anchor="w", pady=2)

        include_average_var = tk.BooleanVar(value=True)
        ttk.Separator(dialog, orient="horizontal").pack(fill="x", padx=18, pady=(6, 8))
        ttk.Checkbutton(
            dialog,
            text="Show Average curve",
            variable=include_average_var
        ).pack(anchor="w", padx=18, pady=(0, 8))

        def set_all(value):
            for var in vars_by_method.values():
                var.set(value)

        quick_frame = tk.Frame(dialog, bg="white")
        quick_frame.pack(fill="x", padx=18, pady=(2, 8))
        ttk.Button(quick_frame, text="Select All", command=lambda: set_all(True)).pack(side="left", padx=(0, 6))
        ttk.Button(quick_frame, text="Clear All", command=lambda: set_all(False)).pack(side="left")
        ttk.Button(
            quick_frame,
            text="Modern Methods",
            command=lambda: [var.set(key in {"ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"}) for key, var in vars_by_method.items()]
        ).pack(side="left", padx=(6, 0))

        def generate_selected_graph():
            selected = [key for key, var in vars_by_method.items() if var.get()]
            if not selected:
                messagebox.showwarning("Select Method", "Please select at least one method.", parent=dialog)
                return
            dialog.destroy()
            try:
                fig = make_all_methods_curve_figure(
                    loading_type,
                    cohesive_model_override=cohesive_model_var.get(),
                    selected_methods=selected,
                    include_average=include_average_var.get()
                )
                plt.show()
            except Exception as e:
                messagebox.showerror("Error", f"สร้าง All Methods Curve ไม่ได้\n\n{e}")

        action_frame = tk.Frame(dialog, bg="white")
        action_frame.pack(fill="x", padx=18, pady=(4, 16))
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(action_frame, text="Generate Graph", style="Primary.TButton", command=generate_selected_graph).pack(side="right", padx=(0, 8))

        dialog.update_idletasks()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - dialog.winfo_width()) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")

    def show_capacity_curve():
        try:
            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            method = method_combo.get()
            cohesive_model = cohesive_combo.get()
            loading_type = loading_combo.get().lower()
            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
                cohesive_model=cohesive_model
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
            "GERRIT run: WPA-01 54-in Pile Cap API(Oct2014)(f\\Model=api(11)\\CPT\\zFricModel=api(11)) | WPA-01 Axial Pile Cap | 54-in Driven open-ended circular pile",
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
            logo_path = Path(resource_path("PTTEP_Logo.svg.png"))
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
            "CPT-CALC-RPT-001 | Interactive Axial Pile Calculation Report\n"
            "for WPA-01 Platform Site\n\n"
            f"Input Sheet P-{page_no:02d}",
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
            "Cohesive model     : API RP 2GEO (October 2014) and API RP 2GEO (October 2014) - Annex C\n"
            "                     (former API RP 2A - 1979)\n\n"
            "Frictional model   : API RP 2GEO (October 2014) CPT-based methods\n\n"
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

    def make_report_intro_fig(D, pile_length, analysis_depth, WT, FS, selected_methods, selected_clay_models, selected_loadings):
        """First page: explain only the methods and outputs selected for this PDF export."""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        # Logo
        try:
            logo_path = Path(resource_path("PTTEP_Logo.svg.png"))
            logo_img = mpimg.imread(str(logo_path))
            logo_ax = fig.add_axes([0.73, 0.845, 0.11, 0.07])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")
            fig.text(0.78, 0.815, "PTTEP International Limited", ha="center", fontsize=7)
        except Exception:
            fig.text(0.78, 0.875, "PTTEP", ha="center", fontsize=18, fontweight="bold", color="#003b71")
            fig.text(0.78, 0.845, "PTTEP International Limited", ha="center", fontsize=7)

        fig.text(0.12, 0.88, "INTERACTIVE AXIAL PILE CALCULATION REPORT", fontsize=12, fontweight="bold", ha="left")
        fig.text(0.12, 0.845, f"Driven Open-Ended Circular Pile - {pile_case_combo.get()}", fontsize=10, ha="left")
        fig.text(0.12, 0.820, "WPA-01 Platform Site", fontsize=9, ha="left")

        # Horizontal line
        ax.plot([0.12, 0.88], [0.795, 0.795], transform=fig.transFigure, color="black", linewidth=0.8)

        method_intro_labels = {
            "API Main Text": "API RP 2GEO Main Text method for frictional soils",
            "API RP 2A (1979-1986)": "Traditional API RP 2A (1979–1986) method for frictional soils",
            "ISO 19901-4:2025": "ISO 19901-4:2025 Unified CPT method for sand",
            "ICP-05": "Method 1: Simplified ICP-05",
            "UWA-05": "Method 2: Offshore UWA-05",
            "Fugro-05": "Method 3: Fugro-05",
            "NGI-05": "Method 4: NGI-05",
        }
        clay_intro_labels = {
            "API RP 2GEO (October 2014)": "API RP 2GEO Main Text clay model",
            "API RP 2GEO (October 2014) - Annex C": "API RP 2GEO Annex C / former API RP 2A-1979 clay model",
        }
        loading_intro_labels = {
            "compression": "Compression capacity",
            "tension": "Tension capacity",
        }

        selected_method_lines = "\n".join(
            f"- {method_intro_labels.get(method, method)}" for method in selected_methods
        )
        selected_clay_lines = "\n".join(
            f"- {clay_intro_labels.get(model, model)}" for model in selected_clay_models
        )
        selected_loading_lines = "\n".join(
            f"- {loading_intro_labels.get(loading, loading.title())}" for loading in selected_loadings
        )

        objective_method_text = ", ".join(
            method_intro_labels.get(method, method) for method in selected_methods
        )

        body = (
            "PROJECT\n\n"
            "WPA-01 Platform Site\n\n"
            "REPORT OBJECTIVE\n\n"
            "To evaluate the axial pile capacity of a driven open-ended circular steel pile using only the analysis methods selected for this PDF export.\n"
            f"Selected frictional/comparison method(s): {objective_method_text}.\n"
            "The output is prepared as a transparent calculation package for checking, comparison, and engineering review.\n\n"
            "SCOPE OF WORK\n\n"
            "The program imports layer-based soil parameters, calculates unit shaft resistance and end bearing resistance, "
            "and produces the selected axial capacity profiles.\n\n"
            "FRICTIONAL / COMPARISON METHODS INCLUDED\n\n"
            f"{selected_method_lines}\n\n"
            "COHESIVE-SOIL MODEL(S) INCLUDED\n\n"
            f"{selected_clay_lines}\n\n"
            "CAPACITY OUTPUTS INCLUDED\n\n"
            f"{selected_loading_lines}\n\n"
            "REPORT OUTPUTS\n\n"
            "- Input parameter tables\n"
            "- Cone resistance profiles for shaft friction and end bearing\n"
            "- Unit shaft friction and unit end-bearing profiles for the selected methods\n"
            "- Selected axial pile capacity curves and calculation summary\n\n"
            "BASIS OF CALCULATION\n\n"
            "Cohesive layers are evaluated only using the cohesive-soil model(s) selected for this report. "
            "Frictional layers are evaluated only using the selected frictional/comparison method(s). "
            "Effective vertical stress is computed using effective unit weight based on the total unit-weight input and a hydrostatic porewater assumption."
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
        info_ax.text(0.62, 0.60, "Prepared output format:\n- A4 PDF report\n- PTTEP engineering-style tables and plots\n- PTTEP-branded presentation layout", fontsize=7.5, ha="left", va="top", linespacing=1.35)

        fig.text(0.12, 0.045, "CPT-CALC-RPT-001 | Interactive Axial Pile Calculation Report for WPA-01 Platform Site", fontsize=6, ha="left", color="#003b71")
        fig.text(0.12, 0.030, "Report Introduction", fontsize=6, ha="left")
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
            logo_path = Path(resource_path("PTTEP_Logo.svg.png"))
            if not logo_path.exists():
                alt_logo = Path(resource_path("PTTEP_Logo.svg(1).png"))
                if alt_logo.exists():
                    logo_path = alt_logo
            logo_img = mpimg.imread(str(logo_path))
            logo_ax = fig.add_axes([0.795, 0.940, 0.125, 0.060])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")
        except Exception:
            fig.text(0.855, 0.966, "PTTEP", fontsize=15, fontweight="bold", color="white", ha="center", va="center")

        fig.text(0.105, 0.970, "CALCULATION SUMMARY", fontsize=16.5, fontweight="bold", color="white", ha="left", va="center")
        fig.text(0.105, 0.946, "Interactive Axial Pile Calculation Report", fontsize=8.8, color="#DCEBFF", ha="left", va="center")
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
        methods = ["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]
        summary_rows = []
        comp_values = []
        tens_values = []

        for method in methods:
            _, comp_summary, _ = calculate_layer_capacity(
                D=D, L=analysis_depth, WT=WT, FS=FS, method=method,
                layer_lines=layer_lines, loading_type="compression",
                cohesive_model=cohesive_combo.get()
            )
            _, tens_summary, _ = calculate_layer_capacity(
                D=D, L=analysis_depth, WT=WT, FS=FS, method=method,
                layer_lines=layer_lines, loading_type="tension",
                cohesive_model=cohesive_combo.get()
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
            ("Cohesive model", cohesive_combo.get()),
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
            "• Results should be reviewed together with soil profile, qc profile, Qshaft/Qbase breakdown, method assumptions, \n"
            "  and project-specific design basis.",
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
            "API Main Text Method  •  API RP 2A (1979-1986)  •  Simplified ICP-05  •  Offshore UWA-05  •  Fugro-05  •  NGI-05",
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
        fig.text(0.105, 0.055, "Interactive Axial Pile Calculator | Version 1.0", fontsize=5.9, ha="left", color=muted)
        fig.text(0.105, 0.042, "CPT-CALC-RPT-001 | WPA-01 Platform Site", fontsize=6.0, ha="left", color=navy)
        fig.text(0.105, 0.029, "Calculation Summary", fontsize=5.9, ha="left", color=muted)
        fig.text(0.895, 0.029, "Generated by PTTEP Internal Engineering Tool", fontsize=5.8, ha="right", color=muted)

        return fig

    def ask_pdf_export_options():
        """Return PDF export selections or None when the user cancels."""
        method_options = [
            ("API Main Text", "API RP 2GEO Main Text"),
            ("API RP 2A (1979-1986)", "Traditional API RP 2A (1979–1986)"),
            ("ISO 19901-4:2025", "ISO 19901-4:2025 Unified CPT"),
            ("ICP-05", "Simplified ICP-05"),
            ("UWA-05", "Offshore UWA-05"),
            ("Fugro-05", "Fugro-05"),
            ("NGI-05", "NGI-05"),
        ]

        dialog = tk.Toplevel(root)
        dialog.title("PDF Export Options")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        result = {"value": None}

        tk.Label(
            dialog, text="Select content for PDF report", bg="white", fg="#003B71",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=20, pady=(16, 3))
        tk.Label(
            dialog,
            text="Choose the comparison methods, clay model and loading graphs to include.",
            bg="white", fg="#64748B", font=("Segoe UI", 8)
        ).pack(anchor="w", padx=20, pady=(0, 10))

        content = tk.Frame(dialog, bg="white")
        content.pack(fill="both", expand=True, padx=20)

        tk.Label(content, text="FRICTIONAL / COMPARISON METHODS", bg="white", fg="#52677F",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))
        method_vars = {}
        for key, label in method_options:
            var = tk.BooleanVar(value=True)
            method_vars[key] = var
            ttk.Checkbutton(content, text=label, variable=var).pack(anchor="w", pady=2)

        quick = tk.Frame(content, bg="white")
        quick.pack(fill="x", pady=(5, 8))

        def set_all_methods(value):
            for var in method_vars.values():
                var.set(value)

        ttk.Button(quick, text="Select All", command=lambda: set_all_methods(True)).pack(side="left", padx=(0, 5))
        ttk.Button(quick, text="Clear All", command=lambda: set_all_methods(False)).pack(side="left")
        ttk.Button(
            quick, text="Modern Methods",
            command=lambda: [var.set(key in {"ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"})
                             for key, var in method_vars.items()]
        ).pack(side="left", padx=(5, 0))

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=(2, 8))
        tk.Label(content, text="COHESIVE-SOIL MODEL PAGES", bg="white", fg="#52677F",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))

        main_clay_var = tk.BooleanVar(value=True)
        annex_clay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(content, text="API RP 2GEO Main Text clay model", variable=main_clay_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(content, text="API RP 2GEO Annex C / former API RP 2A-1979 clay model", variable=annex_clay_var).pack(anchor="w", pady=2)

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=(8, 8))
        tk.Label(content, text="CAPACITY GRAPH PAGES", bg="white", fg="#52677F",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))
        compression_var = tk.BooleanVar(value=True)
        tension_var = tk.BooleanVar(value=True)
        average_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(content, text="Compression graph", variable=compression_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(content, text="Tension graph", variable=tension_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(content, text="Show Average curve", variable=average_var).pack(anchor="w", pady=2)

        def confirm():
            methods = [key for key, var in method_vars.items() if var.get()]
            clay_models = []
            if main_clay_var.get():
                clay_models.append("API RP 2GEO (October 2014)")
            if annex_clay_var.get():
                clay_models.append("API RP 2GEO (October 2014) - Annex C")
            loadings = []
            if compression_var.get():
                loadings.append("compression")
            if tension_var.get():
                loadings.append("tension")

            if not methods:
                messagebox.showwarning("PDF Export", "Please select at least one comparison method.", parent=dialog)
                return
            if not clay_models:
                messagebox.showwarning("PDF Export", "Please select at least one cohesive-soil model.", parent=dialog)
                return
            if not loadings:
                messagebox.showwarning("PDF Export", "Please select at least one capacity graph.", parent=dialog)
                return

            result["value"] = {
                "methods": methods,
                "clay_models": clay_models,
                "loadings": loadings,
                "include_average": average_var.get(),
            }
            dialog.destroy()

        actions = tk.Frame(dialog, bg="white")
        actions.pack(fill="x", padx=20, pady=(12, 16))
        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="Continue to Save", style="Primary.TButton", command=confirm).pack(side="right", padx=(0, 8))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - dialog.winfo_width()) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")
        root.wait_window(dialog)
        return result["value"]

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

            export_options = ask_pdf_export_options()
            if export_options is None:
                return

            selected_methods = export_options["methods"]
            cohesive_models_for_pdf = export_options["clay_models"]
            selected_loadings = export_options["loadings"]
            include_average = export_options["include_average"]

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")]
            )

            if not file_path:
                return

            # Unit-resistance pages follow the selected sand methods and clay models.
            # The first selected clay model remains the calculation fallback where a single override is required.
            profile_clay_model = cohesive_models_for_pdf[0]

            with PdfPages(file_path) as pdf:
                # 1) Introductory page.
                fig = make_report_intro_fig(D, pile_length, analysis_depth, WT, FS, selected_methods, cohesive_models_for_pdf, selected_loadings)
                pdf.savefig(fig)
                plt.close(fig)

                # 2) Input parameter table pages.
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

                # 4) Unit resistance verification profiles using the first selected clay model.
                fig = make_unit_profile_figure(
                    "shaft",
                    loading_type="compression",
                    cohesive_model_override=profile_clay_model,
                    selected_methods=selected_methods,
                    selected_clay_models=cohesive_models_for_pdf
                )
                pdf.savefig(fig)
                plt.close(fig)

                fig = make_unit_profile_figure(
                    "end_bearing",
                    loading_type="compression",
                    cohesive_model_override=profile_clay_model,
                    selected_methods=selected_methods,
                    selected_clay_models=cohesive_models_for_pdf
                )
                pdf.savefig(fig)
                plt.close(fig)

                # 5) Selected capacity curves only.
                # When exactly one friction method and both loadings are selected,
                # combine compression and tension on the same Fugro-style page.
                for clay_model in cohesive_models_for_pdf:
                    if len(selected_methods) == 1 and set(selected_loadings) == {"compression", "tension"}:
                        fig = make_single_method_compression_tension_figure(
                            selected_methods[0],
                            cohesive_model_override=clay_model
                        )
                        pdf.savefig(fig)
                        plt.close(fig)
                    else:
                        for loading_type in selected_loadings:
                            fig = make_all_methods_curve_figure(
                                loading_type,
                                cohesive_model_override=clay_model,
                                selected_methods=selected_methods,
                                include_average=include_average
                            )
                            pdf.savefig(fig)
                            plt.close(fig)

            selected_method_text = ", ".join(selected_methods)
            selected_clay_text = " + ".join(
                "Main Text Clay" if model == "API RP 2GEO (October 2014)" else "Annex C Clay"
                for model in cohesive_models_for_pdf
            )
            messagebox.showinfo(
                "Success",
                "Export PDF Report สำเร็จ\n\n"
                f"Methods: {selected_method_text}\n"
                f"Clay model pages: {selected_clay_text}\n"
                f"Graphs: {', '.join(x.title() for x in selected_loadings)}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Export PDF ไม่ได้\n\n{e}")

    def export_qult_depth_csv():
        """
        Export Qult versus penetration depth for all implemented methods.
        Format intentionally matches the original mentor-approved CSV style:
        metadata header first, blank line, then Qult-vs-depth comparison table.
        Capacity values are exported in MN.
        """
        if IS_DEMO_MODE:
            messagebox.showwarning(
                "Demo Mode",
                "Export Qult Depth CSV is available only for verified PTTEP users."
            )
            return

        try:
            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            analysis_depth = float(entry_analysis_depth.get())
            loading_type = loading_combo.get().lower()
            cohesive_model = cohesive_combo.get()
            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")

            methods = ["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]
            method_curves = {}
            all_depths = set()

            for method in methods:
                depths, qult, _ = calculate_capacity_curve(
                    D=D,
                    WT=WT,
                    FS=FS,
                    method=method,
                    layer_lines=layer_lines,
                    loading_type=loading_type,
                    cohesive_model=cohesive_model
                )

                curve = {}
                for d, q in zip(depths, qult):
                    d = round(float(d), 3)
                    if d <= analysis_depth + 1e-9:
                        curve[d] = float(q)
                        all_depths.add(d)
                method_curves[method] = curve

            if not all_depths:
                messagebox.showwarning("Warning", "ไม่มีข้อมูล Qult สำหรับ Export")
                return

            loading_name = loading_type.capitalize()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv")],
                initialfile=f"Qult_vs_Depth_{loading_type}.csv"
            )
            if not file_path:
                return

            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)

                # --- Metadata block: same style as the first/mentor-approved export ---
                writer.writerow(["Interactive Axial Pile Calculator"])
                writer.writerow(["Export Type", "Qult vs Depth - All Methods"])
                writer.writerow(["Loading Type", loading_name])
                writer.writerow(["Cohesive Model", cohesive_model])
                writer.writerow(["Pile Diameter D (m)", f"{D:.4f}"])
                writer.writerow(["Wall Thickness WT (m)", f"{WT:.4f}"])
                writer.writerow(["Factor of Safety", f"{FS:.1f}"])
                writer.writerow(["Analysis Depth (m)", f"{analysis_depth:.1f}"])
                writer.writerow([])

                # --- Engineering table block ---
                writer.writerow([
                    "Depth (m)",
                    "API Main Text Qult (MN)",
                    "API RP 2A (1979-1986) Qult (MN)",
                    "ICP-05 Qult (MN)",
                    "UWA-05 Qult (MN)",
                    "Fugro-05 Qult (MN)",
                    "NGI-05 Qult (MN)",
                    "Average Qult (MN)",
                    "Lowest Capacity Method",
                    "Lowest Qult (MN)",
                ])

                for depth in sorted(all_depths):
                    values = []
                    valid_values = {}
                    for method in methods:
                        q = method_curves.get(method, {}).get(depth)
                        values.append("" if q is None else f"{q:.3f}")
                        if q is not None:
                            valid_values[method] = q

                    if valid_values:
                        average_q = sum(valid_values.values()) / len(valid_values)
                        lowest_method = min(valid_values, key=valid_values.get)
                        lowest_q = valid_values[lowest_method]
                    else:
                        average_q = None
                        lowest_method = ""
                        lowest_q = None

                    writer.writerow([
                        f"{depth:.3f}",
                        *values,
                        "" if average_q is None else f"{average_q:.3f}",
                        lowest_method,
                        "" if lowest_q is None else f"{lowest_q:.3f}",
                    ])

            messagebox.showinfo("Success", "Export Qult Depth CSV สำเร็จ")

        except Exception as e:
            messagebox.showerror("Error", f"Export Qult Depth CSV ไม่ได้\n\n{e}")



    def _capacity_at_required_depth(depths, capacities, required_capacity, stability_window=5.0):
        """
        Find Required Pile Penetration using all-intersection + 5 m stability logic.

        The program does NOT automatically accept the first intersection. It first
        finds every upward crossing where the selected capacity curve reaches the
        Required Load. Each candidate crossing is then checked over the next
        stability_window metres. The selected penetration is the first crossing
        that remains stable over that 5 m interval.

        Acceptance criteria after each candidate crossing:
        1) Capacity must not fall below the Required Load within the next 5 m.
        2) Capacity at the end of the 5 m check window must be greater than or
           equal to the capacity at the candidate point.

        This avoids selecting a temporary/local intersection where the capacity
        drops again immediately after the selected penetration. If the first
        crossing fails, the program continues to the next crossing.

        Returns (depth, capacity_at_depth) or (None, None) if no valid crossing is found.
        """
        if not depths or not capacities or len(depths) != len(capacities):
            return None, None

        clean = []
        for d, q in zip(depths, capacities):
            try:
                clean.append((float(d), float(q)))
            except Exception:
                pass

        if not clean:
            return None, None

        clean.sort(key=lambda x: x[0])

        def interp_at(target_depth):
            if target_depth <= clean[0][0]:
                return clean[0][1]
            if target_depth >= clean[-1][0]:
                return clean[-1][1]
            for j in range(1, len(clean)):
                d1, q1 = clean[j - 1]
                d2, q2 = clean[j]
                if d1 <= target_depth <= d2:
                    if abs(d2 - d1) < 1e-12:
                        return q2
                    return q1 + (target_depth - d1) * (q2 - q1) / (d2 - d1)
            return None

        def passes_5m_stability_check(candidate_depth):
            candidate_q = interp_at(candidate_depth)
            if candidate_q is None:
                return False

            end_depth = min(candidate_depth + float(stability_window), clean[-1][0])

            check_depths = [candidate_depth]
            for d, _ in clean:
                if candidate_depth < d < end_depth:
                    check_depths.append(d)
            if end_depth > candidate_depth + 1e-9:
                check_depths.append(end_depth)

            tol = 1e-6
            qs = []
            for d in check_depths:
                q = interp_at(d)
                if q is None:
                    return False
                qs.append(q)

                # Capacity must remain above the required load in the next 5 m.
                if q < required_capacity - tol:
                    return False

            # The curve should not be lower at the end of the 5 m check window.
            # Small local wiggles inside the interval are allowed as long as the
            # curve remains above Required Load and ends at or above the candidate.
            if qs[-1] < candidate_q - tol:
                return False

            return True

        # Build candidate list: first-point candidate if already above Required Load,
        # plus every upward crossing from below to equal/above Required Load.
        candidates = []
        d0, q0 = clean[0]
        if q0 >= required_capacity:
            candidates.append((d0, q0))

        for i in range(1, len(clean)):
            d1, q1 = clean[i - 1]
            d2, q2 = clean[i]

            # Only upward crossings are candidates. Downward crossings are rejected.
            if q1 < required_capacity <= q2:
                if abs(q2 - q1) < 1e-12:
                    depth_req = d2
                else:
                    depth_req = d1 + (required_capacity - q1) * (d2 - d1) / (q2 - q1)
                candidates.append((depth_req, required_capacity))

        # Test each crossing. If the first crossing fails, continue to the next one.
        for depth_req, cap_req in candidates:
            if passes_5m_stability_check(depth_req):
                return depth_req, cap_req

        return None, None

    def _interpolate_capacity(depths, capacities, target_depth):
        """Linear interpolation of capacity at a given depth."""
        clean = []
        for d, q in zip(depths, capacities):
            try:
                clean.append((float(d), float(q)))
            except Exception:
                pass
        if not clean:
            return None
        clean.sort(key=lambda x: x[0])

        if target_depth <= clean[0][0]:
            return clean[0][1]
        if target_depth >= clean[-1][0]:
            return clean[-1][1]

        for i in range(1, len(clean)):
            d1, q1 = clean[i - 1]
            d2, q2 = clean[i]
            if d1 <= target_depth <= d2:
                if abs(d2 - d1) < 1e-12:
                    return q2
                return q1 + (target_depth - d1) * (q2 - q1) / (d2 - d1)
        return None

    def _build_average_capacity_curve(D, WT, FS, layer_lines, loading_type, cohesive_model, basis):
        """
        Build average capacity curve from API, ICP, UWA, Fugro and NGI.
        The average is calculated at the common union of all depth points.
        """
        methods = ["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"]
        curves = []
        all_depths = set()

        for method in methods:
            depths, qult, qallow = calculate_capacity_curve(
                D=D,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
                cohesive_model=cohesive_model
            )
            capacities = qallow if basis == "Allowable Capacity" else qult
            if depths and capacities:
                curves.append((depths, capacities))
                for d in depths:
                    all_depths.add(round(float(d), 3))

        avg_depths = []
        avg_caps = []
        for depth in sorted(all_depths):
            vals = []
            for depths, capacities in curves:
                q = _interpolate_capacity(depths, capacities, depth)
                if q is not None:
                    vals.append(float(q))
            if vals:
                avg_depths.append(depth)
                avg_caps.append(sum(vals) / len(vals))

        return avg_depths, avg_caps

    def _required_penetration_crossing_details(depths, capacities, required_load, stability_window=5.0):
        """Return all upward intersections and 5 m stability-check details."""
        clean = []
        for d, q in zip(depths, capacities):
            try:
                clean.append((float(d), float(q)))
            except Exception:
                pass
        if not clean:
            return [], None
        clean.sort(key=lambda x: x[0])

        def interp_at(target_depth):
            if target_depth <= clean[0][0]:
                return clean[0][1]
            if target_depth >= clean[-1][0]:
                return clean[-1][1]
            for j in range(1, len(clean)):
                d1, q1 = clean[j - 1]
                d2, q2 = clean[j]
                if d1 <= target_depth <= d2:
                    if abs(d2 - d1) < 1e-12:
                        return q2
                    return q1 + (target_depth - d1) * (q2 - q1) / (d2 - d1)
            return None

        candidates = []
        d0, q0 = clean[0]
        if q0 >= required_load:
            candidates.append((d0, q0))
        for i in range(1, len(clean)):
            d1, q1 = clean[i - 1]
            d2, q2 = clean[i]
            if q1 < required_load <= q2:
                if abs(q2 - q1) < 1e-12:
                    d_req = d2
                else:
                    d_req = d1 + (required_load - q1) * (d2 - d1) / (q2 - q1)
                candidates.append((d_req, required_load))

        details = []
        selected = None
        for no, (d_req, cap_req) in enumerate(candidates, start=1):
            end_depth = min(d_req + float(stability_window), clean[-1][0])
            check_depths = [d_req]
            for d, _ in clean:
                if d_req < d < end_depth:
                    check_depths.append(d)
            if end_depth > d_req + 1e-9:
                check_depths.append(end_depth)

            qs = [interp_at(d) for d in check_depths]
            qs = [q for q in qs if q is not None]
            min_q = min(qs) if qs else None
            max_q = max(qs) if qs else None
            end_q = qs[-1] if qs else None
            pass_load = (min_q is not None and min_q >= required_load - 1e-6)
            pass_end = (end_q is not None and end_q >= cap_req - 1e-6)
            passed = bool(pass_load and pass_end)
            row = {
                "no": no,
                "depth": d_req,
                "capacity": cap_req,
                "check_start": d_req,
                "check_end": end_depth,
                "min_q": min_q,
                "max_q": max_q,
                "passed": passed,
                "selected": False,
            }
            if passed and selected is None:
                row["selected"] = True
                selected = row
            details.append(row)
        return details, selected

    def _show_required_penetration_intersection(depths, capacities, required_load, required_depth, method_name, basis, loading_type, cohesive_model, stability_window=5.0):
        """Open a full in-program Required Pile Penetration window with chart, details and multiple-intersection table."""
        try:
            clean = []
            for d, q in zip(depths, capacities):
                try:
                    clean.append((float(d), float(q)))
                except Exception:
                    pass
            if not clean:
                return
            clean.sort(key=lambda x: x[0])
            plot_depths = [d for d, _ in clean]
            plot_caps = [q for _, q in clean]
            cap_at_depth = _interpolate_capacity(plot_depths, plot_caps, required_depth)
            if cap_at_depth is None:
                cap_at_depth = required_load
            details, selected = _required_penetration_crossing_details(plot_depths, plot_caps, required_load, stability_window)
            selected = selected or {
                "depth": required_depth,
                "capacity": cap_at_depth,
                "check_start": required_depth,
                "check_end": min(required_depth + stability_window, plot_depths[-1]),
                "min_q": cap_at_depth,
                "max_q": cap_at_depth,
                "passed": True,
            }

            win = tk.Toplevel(root)
            win.title("Required Pile Penetration")
            win.geometry("1480x860")
            win.minsize(1150, 700)
            win.configure(bg="#F4F7FB")

            outer = tk.Frame(win, bg="#F4F7FB")
            outer.pack(fill="both", expand=True, padx=12, pady=12)
            outer.grid_columnconfigure(0, weight=1)
            outer.grid_columnconfigure(1, weight=0)
            outer.grid_rowconfigure(0, weight=1)
            outer.grid_rowconfigure(1, weight=0)

            chart_card = tk.Frame(outer, bg="white", highlightbackground="#E2E8F0", highlightthickness=1)
            chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 10))
            bottom_card = tk.Frame(outer, bg="white", highlightbackground="#E2E8F0", highlightthickness=1)
            bottom_card.grid(row=1, column=0, sticky="ew", padx=(0, 12))
            side_card = tk.Frame(outer, bg="white", width=330, highlightbackground="#E2E8F0", highlightthickness=1)
            side_card.grid(row=0, column=1, rowspan=2, sticky="ns")
            side_card.grid_propagate(False)

            fig, ax = plt.subplots(figsize=(9.5, 6.5), dpi=110)
            ax.plot(plot_caps, plot_depths, marker="o", markersize=3.0, linewidth=2.0, label=f"{method_name} - {basis}")
            ax.axvline(required_load, linestyle="--", linewidth=1.7, color="red", label=f"Required Load = {required_load:.2f} MN")
            ax.axhline(required_depth, linestyle=":", linewidth=1.7, color="red", label=f"Selected Penetration = {required_depth:.2f} m")

            # show all upward intersections in red, and label each one
            if details:
                xs = [required_load for _ in details]
                ys = [r["depth"] for r in details]
                ax.scatter(xs, ys, s=70, color="red", zorder=10, label="Intersection Points")
                for r in details:
                    ax.annotate(
                        f"{r['depth']:.2f} m\n{required_load:.2f} MN",
                        xy=(required_load, r["depth"]),
                        xytext=(14, -8),
                        textcoords="offset points",
                        fontsize=8,
                        color="red",
                        fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", alpha=0.90)
                    )
            else:
                ax.scatter([required_load], [required_depth], s=90, color="red", zorder=10, label="Intersection Point")

            ax.invert_yaxis()
            ax.set_xlabel("Capacity (MN)")
            ax.set_ylabel("Pile Penetration Depth (m)")
            ax.set_title(
                f"Required Load Intersection - {method_name} ({loading_type.capitalize()})\n"
                f"Basis: {basis}  |  Clay Model: {cohesive_model}",
                fontweight="bold"
            )
            ax.grid(True, which="major", linestyle="--", linewidth=0.6, alpha=0.70)
            ax.minorticks_on()
            ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.35)
            ax.text(0.01, 0.02, f"Clay Model: {cohesive_model}", transform=ax.transAxes, fontsize=8, color="#475569", ha="left", va="bottom")
            ax.legend(loc="best", fontsize=8)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

            # Right control/result panel
            tk.Label(side_card, text="Required Pile Penetration", bg="white", fg="#003B71", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(16, 14))

            def add_info(label, value):
                tk.Label(side_card, text=label, bg="white", fg="#334155", font=("Segoe UI", 8)).pack(anchor="w", padx=14)
                box = tk.Label(side_card, text=value, bg="#F8FAFC", fg="#0B1F3A", font=("Segoe UI", 9), anchor="w", relief="solid", bd=1, padx=7, pady=5)
                box.pack(fill="x", padx=14, pady=(3, 9))
                return box

            add_info("Required Load (MN)", f"{required_load:.2f}")
            add_info("Basis", basis)
            add_info("Loading Type", loading_type.capitalize())
            add_info("Method", method_name)
            add_info("Clay Model", cohesive_model)
            add_info("Check Stability Over", f"{float(stability_window):g} m")

            result_box = tk.Frame(side_card, bg="#F0FFF7", highlightbackground="#7AD39B", highlightthickness=1)
            result_box.pack(fill="x", padx=14, pady=(6, 12))
            tk.Label(result_box, text="✅  Penetration Found", bg="#F0FFF7", fg="#0B7A33", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 8))
            tk.Label(result_box, text="Required Pile Penetration:", bg="#F0FFF7", fg="#0B1F3A", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10)
            tk.Label(result_box, text=f"{required_depth:.2f} m", bg="#F0FFF7", fg="#0B7A33", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=10, pady=(0, 8))
            tk.Label(result_box, text="Capacity at Penetration:", bg="#F0FFF7", fg="#0B1F3A", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10)
            tk.Label(result_box, text=f"{cap_at_depth:.2f} MN", bg="#F0FFF7", fg="#0B7A33", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(0, 10))

            tk.Label(side_card, text="Intersection Details", bg="white", fg="#003B71", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(2, 4))
            details_table = ttk.Treeview(side_card, columns=("item", "value"), show="headings", height=7)
            details_table.heading("item", text="Item")
            details_table.heading("value", text="Value")
            details_table.column("item", width=160, anchor="w")
            details_table.column("value", width=120, anchor="e")
            details_table.pack(fill="x", padx=14, pady=(0, 12))
            detail_rows = [
                ("Required Load (MN)", f"{required_load:.2f}"),
                ("Penetration (m)", f"{required_depth:.2f}"),
                ("Capacity at Point (MN)", f"{cap_at_depth:.2f}"),
                ("Check Range (m)", f"{selected['check_start']:.2f} – {selected['check_end']:.2f}"),
                ("Min. Capacity in Range", "-" if selected.get("min_q") is None else f"{selected['min_q']:.2f}"),
                ("Max. Capacity in Range", "-" if selected.get("max_q") is None else f"{selected['max_q']:.2f}"),
                ("Stability Check", "PASS" if selected.get("passed") else "FAIL"),
            ]
            for row in detail_rows:
                details_table.insert("", "end", values=row)

            note = tk.LabelFrame(side_card, text="Note (5 m Stability Check)", bg="#EFF8FF", fg="#003B71", font=("Segoe UI", 8, "bold"), padx=8, pady=6)
            note.pack(fill="x", padx=14, pady=(0, 12))
            tk.Label(note, text="1. Capacity must remain ≥ Required Load\n   within the check range.\n2. The check avoids selecting a temporary\n   local intersection.", bg="#EFF8FF", fg="#334155", justify="left", font=("Segoe UI", 8)).pack(anchor="w")

            # Bottom multiple intersection table
            tk.Label(bottom_card, text=f"Multiple Intersections Found: {len(details)}", bg="white", fg="#003B71", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
            cols = ("no", "depth", "cap", "check", "status")
            tree = ttk.Treeview(bottom_card, columns=cols, show="headings", height=5)
            for col, heading, width in [
                ("no", "No.", 80),
                ("depth", "Penetration (m)", 160),
                ("cap", "Capacity (MN)", 160),
                ("check", f"{float(stability_window):g} m Check", 260),
                ("status", "Status", 140),
            ]:
                tree.heading(col, text=heading)
                tree.column(col, width=width, anchor="center")
            tree.tag_configure("pass", foreground="#0B8F35", font=("Segoe UI", 9, "bold"))
            tree.tag_configure("fail", foreground="#C00000", font=("Segoe UI", 9, "bold"))
            tree.tag_configure("selected", foreground="#0B8F35", font=("Segoe UI", 9, "bold"))
            for r in details:
                if r["passed"]:
                    check_txt = f"PASS (Min: {r['min_q']:.2f} ≥ {required_load:.2f})"
                    status_txt = "Selected" if r.get("selected") else "Passed"
                    tag = "selected" if r.get("selected") else "pass"
                else:
                    min_txt = "-" if r.get("min_q") is None else f"{r['min_q']:.2f}"
                    check_txt = f"FAIL (Min: {min_txt} < {required_load:.2f})"
                    status_txt = "Rejected"
                    tag = "fail"
                tree.insert("", "end", values=(r["no"], f"{r['depth']:.2f}", f"{r['capacity']:.2f}", check_txt, status_txt), tags=(tag,))
            tree.pack(fill="x", padx=10, pady=(0, 10))

        except Exception as e:
            messagebox.showwarning("Warning", f"แสดงจุดตัดบนกราฟไม่ได้\n\n{e}")

    def find_required_penetration_depth():
        """
        Required Penetration Depth Finder:
        user enters a target load and the program finds the first depth where
        selected capacity curve reaches or exceeds that load.
        """
        try:
            required_load = float(required_load_var.get())
            if required_load <= 0:
                messagebox.showwarning("Warning", "Required Load ต้องมากกว่า 0 MN")
                return

            D = float(entry_diameter.get())
            WT = float(entry_wt.get())
            FS = float(entry_fs.get())
            analysis_depth = float(entry_analysis_depth.get())
            loading_choice = required_loading_combo.get()
            if loading_choice == "Selected Loading Type":
                loading_type = loading_combo.get().lower()
            else:
                loading_type = loading_choice.lower()
            clay_model_choice = required_clay_model_combo.get()
            if clay_model_choice == "Selected Clay Model":
                cohesive_model = cohesive_combo.get()
            else:
                cohesive_model = clay_model_choice

            layer_lines = layer_text.get("1.0", tk.END).strip().split("\n")
            basis = required_basis_combo.get()
            method_choice = required_method_combo.get()

            if method_choice == "Selected Method":
                method_name = method_combo.get()
            else:
                method_name = method_choice

            if method_name == "Average":
                depths, capacities = _build_average_capacity_curve(
                    D=D,
                    WT=WT,
                    FS=FS,
                    layer_lines=layer_lines,
                    loading_type=loading_type,
                    cohesive_model=cohesive_model,
                    basis=basis
                )
            else:
                depths, qult, qallow = calculate_capacity_curve(
                    D=D,
                    WT=WT,
                    FS=FS,
                    method=method_name,
                    layer_lines=layer_lines,
                    loading_type=loading_type,
                    cohesive_model=cohesive_model
                )
                capacities = qallow if basis == "Allowable Capacity" else qult

            filtered = [(d, q) for d, q in zip(depths, capacities) if float(d) <= analysis_depth + 1e-9]
            if not filtered:
                messagebox.showwarning("Warning", "ไม่มีข้อมูล Capacity Curve สำหรับหา Required Depth")
                return

            f_depths = [d for d, _ in filtered]
            f_caps = [q for _, q in filtered]
            stability_window = float(required_stability_window_var.get() or 5.0)
            if stability_window <= 0:
                messagebox.showwarning("Warning", "Check Stability Over ต้องมากกว่า 0 m")
                return

            depth_req, cap_at_depth = _capacity_at_required_depth(f_depths, f_caps, required_load, stability_window=stability_window)

            if depth_req is None:
                max_capacity = max(f_caps)
                max_depth = f_depths[f_caps.index(max_capacity)]
                required_depth_result_var.set("Required Pile Penetration: Not reached")
                required_capacity_result_var.set(f"Max {basis}: {max_capacity:.2f} MN at {max_depth:.2f} m")
                messagebox.showwarning(
                    "Required Depth Not Reached",
                    f"Required Load = {required_load:.2f} MN\n"
                    f"Maximum {basis} = {max_capacity:.2f} MN at {max_depth:.2f} m\n\n"
                    "Required load exceeds the calculated pile capacity within the analysis depth."
                )
                return

            required_depth_result_var.set(f"Required Pile Penetration: {depth_req:.2f} m")
            required_capacity_result_var.set(f"{basis} at Penetration: {cap_at_depth:.2f} MN")

            _show_required_penetration_intersection(
                f_depths,
                f_caps,
                required_load,
                depth_req,
                method_name,
                basis,
                loading_type,
                cohesive_model,
                stability_window=stability_window
            )



        except Exception as e:
            messagebox.showerror("Error", f"หา Required Penetration Depth ไม่ได้\n\n{e}")

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
                    "Depth Range (m)",
                    "Soil",
                    "Behaviour",
                    "gamma (kN/m3)",
                    "gamma_eff (kN/m3)",
                    "p0_layer (kPa)",
                    "cum_p0 (kPa)",
                    "cu (kPa)",
                    "qc_f (MPa)",
                    "qc_eb (MPa)",
                    "delta_cv (deg)",
                    "K0 (-)",
                    "flim (kPa)",
                    "qlim (MPa)",
                    "Used Parameter",
                    "alpha (-)",
                    "Unit Shaft (kPa)",
                    "Unit End Bearing (kPa)",
                    "Layer Qshaft (kN)",
                    "Cum. Qshaft (kN)",
                    "Qbase (kN)",
                    "Qult (kN)"
                ])
                writer.writerows(results)

            messagebox.showinfo("Success", "Export CSV สำเร็จ")


    root = tk.Tk()
    configure_modern_scrollbar_style(root)
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    root.title("Interactive Axial Pile Calculator")
    root.geometry("1500x860")
    root.minsize(980, 680)
    root.configure(bg="#F4F7FB")

    # User-defined Annex C cu/sigma'v0 range for preliminary high-plastic NC screening.
    annex_c_ratio_min_var = tk.StringVar(value="0.22")
    annex_c_ratio_max_var = tk.StringVar(value="0.27")

    # Required penetration depth finder inputs/results.
    required_load_var = tk.StringVar(value="")
    required_clay_model_var = tk.StringVar(value="Selected Clay Model")
    required_depth_result_var = tk.StringVar(value="Required Pile Penetration: -")
    required_capacity_result_var = tk.StringVar(value="Capacity at Penetration: -")
    required_stability_window_var = tk.StringVar(value="5")

    def apply_annex_c_ratio_settings(*_args):
        try:
            r_min = float(annex_c_ratio_min_var.get())
            r_max = float(annex_c_ratio_max_var.get())
            set_annex_c_high_plastic_ratio_range(r_min, r_max)
        except Exception:
            set_annex_c_high_plastic_ratio_range(0.22, 0.27)

    annex_c_ratio_min_var.trace_add("write", apply_annex_c_ratio_settings)
    annex_c_ratio_max_var.trace_add("write", apply_annex_c_ratio_settings)
    apply_annex_c_ratio_settings()

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
        font=("Segoe UI", 8, "bold"),
        background="#EAF2FF",
        foreground="#003B71",
        relief="flat",
        padding=(4, 6)
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
        text="Interactive Axial Pile Calculator",
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
    left_container = tk.Frame(main_frame, bg="#F4F7FB", width=230)
    left_container.pack(side="left", fill="y", padx=(0, 14))
    left_container.pack_propagate(False)

    left_canvas = tk.Canvas(
        left_container,
        width=220,
        bg="#F4F7FB",
        highlightthickness=0,
        bd=0,
        relief="flat"
    )

    left_scrollbar = ctk.CTkScrollbar(
        left_container,
        orientation="vertical",
        command=left_canvas.yview,
        width=8,
        corner_radius=20,
        button_color="#B8C4D6",
        button_hover_color="#8EA4C3",
        fg_color="#F4F7FB"
    )

    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    left_scrollbar.pack(side="right", fill="y", padx=0, pady=0)
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

    right_card, right_frame = make_card(main_frame, "Summary Result", width=260)
    right_card.pack(side="right", fill="y")

    middle_card, middle_frame = make_card(main_frame, "Layer Input and Calculation")
    middle_card.pack(side="left", fill="both", expand=True, padx=(0, 14))

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
        values=["API Main Text", "API RP 2A (1979-1986)", "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05"],
        width=17,
        style="Modern.TCombobox"
    )
    method_combo.pack(fill="x", pady=(3, 8))
    method_combo.current(2)

    tk.Label(left_frame, text="Cohesive Model", bg="white", fg="#334155", font=("Segoe UI", 9)).pack(anchor="w")
    cohesive_combo = ttk.Combobox(
        left_frame,
        values=["API RP 2GEO (October 2014)", "API RP 2GEO (October 2014) - Annex C"],
        width=17,
        style="Modern.TCombobox"
    )
    cohesive_combo.pack(fill="x", pady=(3, 8))
    cohesive_combo.current(0)

    tk.Label(
        left_frame,
        text="Range of High Plastic cu/σ′v0",
        bg="white",
        fg="#334155",
        font=("Segoe UI", 9)
    ).pack(anchor="w")

    annex_ratio_frame = tk.Frame(left_frame, bg="white")
    annex_ratio_frame.pack(fill="x", pady=(3, 2))

    entry_annex_ratio_min = ttk.Entry(
        annex_ratio_frame,
        width=8,
        textvariable=annex_c_ratio_min_var,
        style="Modern.TEntry"
    )
    entry_annex_ratio_min.pack(side="left", fill="x", expand=True)

    tk.Label(
        annex_ratio_frame,
        text=" to ",
        bg="white",
        fg="#64748B",
        font=("Segoe UI", 8)
    ).pack(side="left")

    entry_annex_ratio_max = ttk.Entry(
        annex_ratio_frame,
        width=8,
        textvariable=annex_c_ratio_max_var,
        style="Modern.TEntry"
    )
    entry_annex_ratio_max.pack(side="left", fill="x", expand=True)

    tk.Label(
        left_frame,
        text="Used only for Annex C when PI/LL are unavailable.",
        bg="white",
        fg="#64748B",
        font=("Segoe UI", 7)
    ).pack(anchor="w", pady=(0, 8))

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
    ttk.Button(left_frame, text="Engineering Advisor", width=24, command=show_detailed_engineering_advisor, style="Primary.TButton").pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Report qc Profile", width=24, style="Modern.TButton", command=show_report_qc_profile).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Single Method Curve", width=24, style="Modern.TButton", command=show_capacity_curve).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="All Methods Compression", width=24, style="Modern.TButton", command=lambda: show_all_methods_curve("compression")).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="All Methods Tension", width=24, style="Modern.TButton", command=lambda: show_all_methods_curve("tension")).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Unit Friction Profile", width=24, style="Modern.TButton", command=show_unit_friction_profile).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Unit End Bearing Profile", width=24, style="Modern.TButton", command=show_unit_end_bearing_profile).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Export PDF Report", width=24, style="Modern.TButton", command=export_pdf_report).pack(fill="x", pady=4)
    ttk.Button(left_frame, text="Export Qult Depth CSV", width=24, style="Modern.TButton", command=export_qult_depth_csv).pack(fill="x", pady=4)

    # =========================
    # REQUIRED PENETRATION DEPTH FINDER
    # Open inputs in a dedicated dialog instead of displaying them permanently.
    # =========================
    required_basis_combo = None
    required_loading_combo = None
    required_method_combo = None
    required_clay_model_combo = None

    def open_required_penetration_dialog():
        nonlocal required_basis_combo, required_loading_combo, required_method_combo, required_clay_model_combo

        win = tk.Toplevel(root)
        win.title("Required Pile Penetration")
        win.geometry("480x650")
        win.minsize(440, 580)
        win.configure(bg="#F4F7FB")
        win.transient(root)
        win.grab_set()

        card = tk.Frame(win, bg="white", padx=22, pady=18, highlightbackground="#D9E2EC", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(card, text="Required Pile Penetration", bg="white", fg="#003B71",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(card, text="Enter the design requirement and select the calculation basis.",
                 bg="white", fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 14))

        def field_label(text):
            tk.Label(card, text=text, bg="white", fg="#334155",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(7, 2))

        field_label("Required Load (MN)")
        required_load_entry = ttk.Entry(card, textvariable=required_load_var, style="Modern.TEntry")
        required_load_entry.pack(fill="x", ipady=3)

        field_label("Basis")
        required_basis_combo = ttk.Combobox(
            card, values=["Allowable Capacity", "Ultimate Capacity"],
            state="readonly", style="Modern.TCombobox"
        )
        required_basis_combo.pack(fill="x")
        required_basis_combo.current(0)

        field_label("Loading Type")
        required_loading_combo = ttk.Combobox(
            card, values=["Selected Loading Type", "Compression", "Tension"],
            state="readonly", style="Modern.TCombobox"
        )
        required_loading_combo.pack(fill="x")
        required_loading_combo.current(0)

        field_label("Method")
        required_method_combo = ttk.Combobox(
            card,
            values=["Selected Method", "API Main Text", "API RP 2A (1979-1986)",
                    "ISO 19901-4:2025", "ICP-05", "UWA-05", "Fugro-05", "NGI-05", "Average"],
            state="readonly", style="Modern.TCombobox"
        )
        required_method_combo.pack(fill="x")
        required_method_combo.current(0)

        field_label("Clay Model")
        required_clay_model_combo = ttk.Combobox(
            card,
            values=["Selected Clay Model", "API RP 2GEO (October 2014)",
                    "API RP 2GEO (October 2014) - Annex C"],
            state="readonly", style="Modern.TCombobox"
        )
        required_clay_model_combo.pack(fill="x")
        required_clay_model_combo.current(0)

        field_label("Check Stability Over")
        stability_row = tk.Frame(card, bg="white")
        stability_row.pack(fill="x")
        required_stability_entry = ttk.Entry(
            stability_row, textvariable=required_stability_window_var,
            style="Modern.TEntry", width=10
        )
        required_stability_entry.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Label(stability_row, text=" m", bg="white", fg="#334155",
                 font=("Segoe UI", 9)).pack(side="left")

        result_box = tk.Frame(card, bg="#F8FBFF", padx=10, pady=9,
                              highlightbackground="#D7E6F5", highlightthickness=1)
        result_box.pack(fill="x", pady=(16, 10))
        tk.Label(result_box, textvariable=required_depth_result_var, bg="#F8FBFF",
                 fg="#0B1F3A", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(result_box, textvariable=required_capacity_result_var, bg="#F8FBFF",
                 fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        button_row = tk.Frame(card, bg="white")
        button_row.pack(fill="x", pady=(8, 0))
        ttk.Button(button_row, text="Cancel", style="Modern.TButton",
                   command=win.destroy).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(button_row, text="Calculate Penetration", style="Primary.TButton",
                   command=find_required_penetration_depth).pack(side="left", fill="x", expand=True, padx=(5, 0))

        required_load_entry.bind("<Return>", lambda event: find_required_penetration_depth())
        required_load_entry.bind("<KP_Enter>", lambda event: find_required_penetration_depth())
        required_stability_entry.bind("<Return>", lambda event: find_required_penetration_depth())
        required_stability_entry.bind("<KP_Enter>", lambda event: find_required_penetration_depth())
        required_load_entry.focus_set()

    ttk.Button(
        left_frame, text="Required Pile Penetration", width=24,
        style="Primary.TButton", command=open_required_penetration_dialog
    ).pack(fill="x", pady=4)

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
        "used", "alpha", "unit_shaft", "unit_end_bearing", "qshaft_layer", "qshaft_cum", "qbase", "qult"
    )

    # Table wrapper: keeps the horizontal scrollbar visible on small screens.
    table_frame = tk.Frame(middle_frame, bg="white")
    table_frame.pack(fill="both", expand=True, pady=(10, 0))
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    table = ttk.Treeview(table_frame, columns=columns, show="headings", height=17)

    headings = {
        "depth_range": "Depth (m)",
        "soil": "Soil",
        "behavior": "Behaviour",
        "gamma": "γ (kN/m³)",
        "gamma_eff": "γ′ (kN/m³)",
        "p0_layer": "p′0 layer (kPa)",
        "cum_p0": "Cum. p′0 (kPa)",
        "cu": "cu (kPa)",
        "qc_f": "qc,f (MPa)",
        "qc_eb": "qc,eb (MPa)",
        "delta": "δcv (°)",
        "k0": "K0 (-)",
        "flim": "flim (kPa)",
        "qlim": "qlim (MPa)",
        "used": "Used",
        "alpha": "α (-)",
        "unit_shaft": "Unit Shaft (kPa)",
        "unit_end_bearing": "Unit End Bearing (kPa)",
        "qshaft_layer": "Layer Qshaft (kN)",
        "qshaft_cum": "Cum. Qshaft (kN)",
        "qbase": "Qbase (kN)",
        "qult": "Qult (kN)"
    }

    widths = {
        "depth_range": 100,
        "soil": 90,
        "behavior": 100,
        "gamma": 100,
        "gamma_eff": 110,
        "p0_layer": 120,
        "cum_p0": 120,
        "cu": 90,
        "qc_f": 100,
        "qc_eb": 100,
        "delta": 80,
        "k0": 70,
        "flim": 90,
        "qlim": 90,
        "used": 120,
        "alpha": 80,
        "unit_shaft": 130,
        "unit_end_bearing": 170,
        "qshaft_layer": 130,
        "qshaft_cum": 130,
        "qbase": 100,
        "qult": 100
    }

    for col in columns:
        table.heading(col, text=headings[col])
        table.column(col, width=widths[col], anchor="center", stretch=False)

    table_xscroll = ctk.CTkScrollbar(
        table_frame,
        orientation="horizontal",
        command=table.xview,
        height=8,
        corner_radius=20,
        button_color="#B8C4D6",
        button_hover_color="#8EA4C3",
        fg_color="#F4F7FB"
    )
    table.configure(xscrollcommand=table_xscroll.set)

    table.grid(row=0, column=0, sticky="nsew")
    table_xscroll.grid(row=1, column=0, sticky="ew", pady=(2, 0), padx=0)

    def _on_table_shift_mousewheel(event):
        table.xview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    table.bind("<Shift-MouseWheel>", _on_table_shift_mousewheel)

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

    summary_scrollbar = ctk.CTkScrollbar(
        right_frame,
        orientation="vertical",
        command=summary_canvas.yview,
        width=8,
        corner_radius=20,
        button_color="#B8C4D6",
        button_hover_color="#8EA4C3",
        fg_color="white"
    )
    summary_scrollbar.pack(side="right", fill="y", padx=0, pady=0)

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
            ("Cohesive", "cohesive_model"),
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


    def add_text_block(parent, title, key, accent="#003B71", bg="#FFFFFF"):
        block = tk.Frame(parent, bg=bg)
        block.pack(fill="x", pady=(0, 8))

        tk.Label(
            block,
            text=title,
            bg=bg,
            fg="#64748B",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        summary_vars[key] = tk.StringVar(value="-")
        tk.Label(
            block,
            textvariable=summary_vars[key],
            bg=bg,
            fg=accent,
            font=("Segoe UI", 9, "bold"),
            justify="left",
            anchor="w",
            wraplength=210
        ).pack(anchor="w", fill="x", pady=(2, 0))

    def add_method_advisor_card(parent):
        section = tk.Frame(parent, bg="#D7E3F3")
        section.pack(fill="x", pady=(0, 8), padx=(0, 4))

        inner = tk.Frame(section, bg="#FFFFFF", padx=10, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(
            inner,
            text="METHOD ADVISOR",
            bg="#FFFFFF",
            fg="#003B71",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 8))

        add_text_block(inner, "PRIMARY DESIGN METHOD", "advisor_primary_method", accent="#0B1F3A")
        add_text_block(inner, "SITE ASSESSMENT", "advisor_site_basis", accent="#0B1F3A")
        add_text_block(inner, "METHOD APPLICABILITY", "advisor_applicability", accent="#0B1F3A")
        add_text_block(inner, "CAPACITY COMPARISON", "advisor_capacity_comparison", accent="#0B1F3A")
        add_text_block(inner, "WHY THIS METHOD", "advisor_why_primary", accent="#0B1F3A")
        add_text_block(inner, "SECONDARY / ALSO CHECK", "advisor_secondary_methods", accent="#003B71")
        add_text_block(inner, "LOWEST CAPACITY CHECK", "advisor_lowest_capacity", accent="#003B71")
        add_text_block(inner, "METHOD SPREAD", "advisor_spread", accent="#003B71")
        add_text_block(inner, "ENGINEERING WARNING", "advisor_warning", accent="#9A3412")

    add_kpi_card(summary_inner, "ULTIMATE CAPACITY", "Qult", "Qult")
    add_kpi_card(summary_inner, "ALLOWABLE CAPACITY", "Qallow", "Qallow")
    add_kpi_card(summary_inner, "SHAFT CAPACITY", "Qshaft", "Qshaft")
    add_kpi_card(summary_inner, "BASE CAPACITY", "Qbase", "Qbase")

    add_method_advisor_card(summary_inner)



    root.mainloop()
