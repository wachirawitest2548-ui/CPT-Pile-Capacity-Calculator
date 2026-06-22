import math

PA = 100.0
DCPT = 0.036
INTEGRATION_STEP = 0.25
GAMMA_W = 10.0  # kN/m3, seawater approx.


def pile_area(D):
    return math.pi * D**2 / 4


def pile_perimeter(D):
    return math.pi * D


def pile_inside_diameter(D, WT):
    return D - 2 * WT


def pile_displacement_ratio(D, WT):
    Di = pile_inside_diameter(D, WT)
    if Di <= 0:
        raise ValueError("Wall thickness มากเกินไป ทำให้ Di <= 0")
    return 1 - (Di / D) ** 2


def clean_value(value):
    value = str(value).strip()
    if value in ["", "-", "–", "—"]:
        return ""
    return value


def parse_float(value):
    value = clean_value(value)
    if value == "":
        return None
    return float(value)


def interp(v_top, v_bot, z1, z2, z):
    if v_top is None or v_bot is None:
        return None
    if z2 == z1:
        return v_top

    r = (z - z1) / (z2 - z1)
    r = max(0.0, min(1.0, r))
    return v_top + r * (v_bot - v_top)


def layer_value(layer, key, z):
    if key == "gamma":
        return interp(layer["gamma_top"], layer["gamma_bot"], layer["from_depth"], layer["to_depth"], z)

    if key == "cu":
        return interp(layer["cu_top"], layer["cu_bot"], layer["from_depth"], layer["to_depth"], z)

    if key == "qc_f":
        return layer["qc_f"]

    if key == "qc_eb":
        return layer["qc_eb"]

    return None


def parse_layer_lines(lines):
    layers = []

    for line in lines:
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) != 14:
            raise ValueError(
                "Format ต้องเป็น: from_depth,to_depth,soil_type,behavior,"
                "gamma_top,gamma_bot,cu_top,cu_bot,qc_f,qc_eb,delta_cv,k0,flim,qlim"
            )

        (
            from_depth,
            to_depth,
            soil_type,
            behavior,
            gamma_top,
            gamma_bot,
            cu_top,
            cu_bot,
            qc_f,
            qc_eb,
            delta_cv,
            k0,
            flim,
            qlim,
        ) = parts

        qc_f_value = parse_float(qc_f)
        qc_eb_value = parse_float(qc_eb)
        qlim_value = parse_float(qlim)

        layer = {
            "from_depth": float(from_depth),
            "to_depth": float(to_depth),
            "soil_type": soil_type.lower(),
            "behavior": behavior.lower(),
            "gamma_top": parse_float(gamma_top),
            "gamma_bot": parse_float(gamma_bot),
            "cu_top": parse_float(cu_top),
            "cu_bot": parse_float(cu_bot),
            "qc_f": qc_f_value * 1000 if qc_f_value is not None else None,
            "qc_eb": qc_eb_value * 1000 if qc_eb_value is not None else None,
            "delta_cv": parse_float(delta_cv),
            "k0": parse_float(k0),
            "flim": parse_float(flim),
            "qlim": qlim_value * 1000 if qlim_value is not None else None,
        }

        z_mid = 0.5 * (layer["from_depth"] + layer["to_depth"])
        layer["gamma"] = layer_value(layer, "gamma", z_mid)
        layer["cu"] = layer_value(layer, "cu", z_mid)

        layers.append(layer)

    layers.sort(key=lambda x: x["from_depth"])
    return layers


def effective_stress_at_depth(layers, z):
    """
    p'0 = effective vertical stress.
    Input gamma is assumed as total/bulk unit weight from report.
    Therefore gamma' = gamma_total - gamma_w.
    """
    stress = 0.0

    for layer in layers:
        z1 = layer["from_depth"]
        z2 = layer["to_depth"]

        if z <= z1:
            continue

        za = z1
        zb = min(z, z2)

        if zb > za:
            ga = layer_value(layer, "gamma", za)
            gb = layer_value(layer, "gamma", zb)

            if ga is None or gb is None:
                raise ValueError("gamma หายไปในบาง layer")

            ga_eff = max(ga - GAMMA_W, 0.1)
            gb_eff = max(gb - GAMMA_W, 0.1)

            stress += 0.5 * (ga_eff + gb_eff) * (zb - za)

        if z <= z2:
            break

    return max(stress, 1.0)


def get_layer_at_depth(layers, z):
    for layer in layers:
        if layer["from_depth"] <= z <= layer["to_depth"]:
            return layer
    return layers[-1]


def method_parameters(method, Ar, loading_type="compression"):
    if method == "ICP-05":
        if loading_type == "compression":
            return {"a": 0.1, "b": 0.2, "c": 0.4, "d": 1, "e": 0, "u": 0.023, "v": 4 * math.sqrt(Ar)}
        return {"a": 0.1, "b": 0.2, "c": 0.4, "d": 1, "e": 0, "u": 0.016, "v": 4 * math.sqrt(Ar)}

    if method == "UWA-05":
        if loading_type == "compression":
            return {"a": 0, "b": 0.3, "c": 0.5, "d": 1, "e": 0, "u": 0.030, "v": 2}
        return {"a": 0, "b": 0.3, "c": 0.5, "d": 1, "e": 0, "u": 0.022, "v": 2}

    if method == "Fugro-05":
        if loading_type == "compression":
            return {"a": 0.05, "b": 0.45, "c": 0.90, "d": 0, "e": 1, "u": 0.043, "v": 2 * math.sqrt(Ar)}
        return {"a": 0.15, "b": 0.42, "c": 0.85, "d": 0, "e": 0, "u": 0.025, "v": 2 * math.sqrt(Ar)}

    raise ValueError("Method ไม่ถูกต้อง")


def unit_shaft_cohesive(layer, z, layers):
    cu = layer_value(layer, "cu", z)
    if cu is None:
        return 0.0

    p0 = effective_stress_at_depth(layers, z)
    psi = cu / p0

    if psi <= 1:
        alpha = 0.5 * psi ** (-0.5)
    else:
        alpha = 0.5 * psi ** (-0.25)

    alpha = min(alpha, 1.0)
    unit_shaft = alpha * cu

    if layer["flim"] is not None:
        unit_shaft = min(unit_shaft, layer["flim"])

    return unit_shaft


def relative_density_method4(qc, z, layers):
    p0 = effective_stress_at_depth(layers, z)
    Dr = 0.4 * math.log(qc / (22 * math.sqrt(p0 * PA)))
    return max(Dr, 0.1)


# =========================
# API RP 2GEO MAIN TEXT / SIMPLIFIED METHOD
# =========================
# This method is added as a reference / baseline method.
# Clay:
#   shaft: f = alpha * su
#   base : q = 9 * su
# Sand:
#   shaft: f = beta * p'0
#   base : q = Nq * p'0,tip
#
# API Table 1 gives beta and Nq by sand density/state. Since most input files
# use only "Sand" as soil type, the program estimates relative density from CPT
# cone resistance and then classifies the sand state automatically.
#
# Important:
# - This Dr correlation is an engineering correlation used only for automatic
#   selection of beta and Nq.
# - API Main Text itself requires engineering judgment / soil interpretation
#   for selecting the sand density state.
# =========================

def estimate_dr_percent_from_qc(qc_kpa):
    """
    Estimate relative density Dr (%) from CPT cone resistance.

    qc_kpa : cone resistance in kPa

    Project-calibrated approximation based on WPA-01 / Fugro relative
    density profile trend:
        Dr(%) = 18 + 1.55 * qc(MPa)

    This is NOT an API RP 2GEO required equation. It is used only to
    automatically classify sand density for API Main Text beta / Nq
    selection when the input file only states "Sand".
    """
    if qc_kpa is None or qc_kpa <= 0:
        return 0.0

    qc_mpa = qc_kpa / 1000.0
    dr = 18.0 + 1.55 * qc_mpa

    return max(0.0, min(100.0, dr))


def api_main_text_sand_state_from_dr(dr_percent):
    """
    Classify sand state and return API Table 1 parameters.

    Returns:
        sand_state, beta, Nq, flim_table_kpa, qlim_table_kpa

    Classification used in this program:
        Dr < 30%       : Loose Sand
        30% <= Dr <55% : Medium Dense Sand
        55% <= Dr <75% : Dense Sand
        Dr >= 75%      : Very Dense Sand

    API Table 1 values used here:
        Medium dense sand-silt : beta=0.29, flim=67 kPa, Nq=12, qlim=3 MPa
        Medium dense sand      : beta=0.37, flim=81 kPa, Nq=20, qlim=5 MPa
        Dense sand / sand-silt : beta=0.46, flim=96 kPa, Nq=40, qlim=10 MPa
        Very dense sand        : beta=0.56, flim=115 kPa, Nq=50, qlim=12 MPa

    Note:
        Loose / very loose sand is not directly applicable in API Table 1.
        For continuity in automatic plotting, Loose Sand is mapped to the most
        conservative applicable row. For final design, review manually.
    """
    if dr_percent < 30:
        return "Loose Sand", 0.29, 12, 67.0, 3000.0

    if dr_percent < 55:
        return "Medium Dense Sand", 0.37, 20, 81.0, 5000.0

    if dr_percent < 75:
        return "Dense Sand", 0.46, 40, 96.0, 10000.0

    return "Very Dense Sand", 0.56, 50, 115.0, 12000.0


def api_main_text_sand_params_from_qc(qc_kpa):
    dr_percent = estimate_dr_percent_from_qc(qc_kpa)
    sand_state, beta, Nq, flim_table, qlim_table = api_main_text_sand_state_from_dr(dr_percent)
    return {
        "Dr_percent": dr_percent,
        "sand_state": sand_state,
        "beta": beta,
        "Nq": Nq,
        "flim_table": flim_table,   # kPa
        "qlim_table": qlim_table,   # kPa
    }


def unit_shaft_frictional(layer, z, D, L, WT, layers, method, loading_type="compression"):
    qc_f = layer_value(layer, "qc_f", z)
    if qc_f is None:
        return 0.0

    Ar = pile_displacement_ratio(D, WT)
    p0 = effective_stress_at_depth(layers, z)

    delta_cv = layer["delta_cv"] if layer["delta_cv"] is not None else 28.8
    tan_delta_cv = math.tan(math.radians(delta_cv))

    if method in ["ICP-05", "UWA-05", "Fugro-05"]:
        p = method_parameters(method, Ar, loading_type)

        term1 = p["u"] * qc_f
        term2 = (p0 / PA) ** p["a"]
        term3 = Ar ** p["b"]
        term4 = max((L - z) / D, p["v"]) ** (-p["c"])
        term5 = tan_delta_cv ** p["d"]
        term6 = min(((L - z) / D) * (1 / p["v"]), 1) ** p["e"]

        unit_shaft = max(term1 * term2 * term3 * term4 * term5 * term6, 0)

    elif method == "NGI-05":
        Dr = relative_density_method4(qc_f, z, layers)
        Fsig = (p0 / PA) ** 0.25
        FDr = 2.1 * (Dr - 0.1) ** 1.7

        if loading_type == "compression":
            unit_shaft = 1.3 * (z / L) * PA * Fsig * FDr
        else:
            unit_shaft = (z / L) * PA * Fsig * FDr

        # API RP 2GEO Method 4 lower-bound requirement:
        # Eq. C.13 / C.14 states ft(z) and fc(z) shall be greater than 0.1 p'0(z).
        # This prevents low-qc frictional layers from producing zero unit shaft resistance.
        unit_shaft = max(unit_shaft, 0.1 * p0)

    elif method == "API Main Text":
        params = api_main_text_sand_params_from_qc(qc_f)
        beta = params["beta"]

        # API Main Text simplified sand shaft resistance:
        #     f = beta * p'0
        # Then cap by API Table 1 limiting unit shaft friction.
        # If the input CSV also provides flim, use the smaller of the two.
        unit_shaft = beta * p0
        unit_shaft = max(unit_shaft, 0)

        table_flim = params["flim_table"]
        if table_flim is not None:
            unit_shaft = min(unit_shaft, table_flim)

    else:
        raise ValueError("Method ไม่ถูกต้อง")

    if layer["flim"] is not None:
        unit_shaft = min(unit_shaft, layer["flim"])

    return unit_shaft


def integrate_layer_shaft(layer, D, L, WT, layers, method, loading_type):
    z1 = layer["from_depth"]
    z2 = min(layer["to_depth"], L)

    if z2 <= z1:
        return 0.0, 0.0

    perimeter = pile_perimeter(D)
    total_qshaft = 0.0
    weighted_unit = 0.0
    total_dz = 0.0

    z = z1
    while z < z2:
        za = z
        zb = min(z + INTEGRATION_STEP, z2)
        z_mid = 0.5 * (za + zb)
        dz = zb - za

        if layer["behavior"] == "cohesive":
            unit = unit_shaft_cohesive(layer, z_mid, layers)
        elif layer["behavior"] == "frictional":
            unit = unit_shaft_frictional(layer, z_mid, D, L, WT, layers, method, loading_type)
        else:
            raise ValueError("behavior ต้องเป็น cohesive หรือ frictional")

        total_qshaft += unit * perimeter * dz
        weighted_unit += unit * dz
        total_dz += dz
        z = zb

    avg_unit = weighted_unit / total_dz if total_dz > 0 else 0.0
    return avg_unit, total_qshaft


def qc_eb_average_around_tip(layers, L, D):
    z_min = max(0, L - 1.5 * D)
    z_max = L + 1.5 * D

    total_qc = 0.0
    total_dz = 0.0

    for layer in layers:
        za = max(layer["from_depth"], z_min)
        zb = min(layer["to_depth"], z_max)

        if zb <= za:
            continue

        z = za
        while z < zb:
            z_next = min(z + INTEGRATION_STEP, zb)
            z_mid = 0.5 * (z + z_next)
            dz = z_next - z
            qc_eb = layer_value(layer, "qc_eb", z_mid)

            if qc_eb is not None:
                total_qc += qc_eb * dz
                total_dz += dz

            z = z_next

    if total_dz == 0:
        return None

    return total_qc / total_dz


def end_bearing_frictional(method, qc_eb_av, D, WT, layers, L, tip_layer):
    Ar = pile_displacement_ratio(D, WT)

    if method == "ICP-05":
        q_unit = qc_eb_av * (0.5 - 0.25 * math.log10(D / DCPT))
        q_unit = max(q_unit, 0.15 * qc_eb_av)

    elif method == "UWA-05":
        q_unit = qc_eb_av * (0.15 + 0.45 * Ar)

    elif method == "Fugro-05":
        q_unit = 8.5 * PA * (qc_eb_av / PA) ** 0.5 * Ar ** 0.25

    elif method == "NGI-05":
        Dr = relative_density_method4(qc_eb_av, L, layers)
        q_unit = 0.7 * qc_eb_av / (1 + 3 * Dr ** 2)

    elif method == "API Main Text":
        # API Main Text simplified sand end bearing:
        #     q = Nq * p'0,tip
        # Then cap by API Table 1 limiting unit end bearing.
        # If the input CSV also provides qlim, use the smaller of the two.
        qc_for_state = layer_value(tip_layer, "qc_eb", L)
        if qc_for_state is None:
            qc_for_state = layer_value(tip_layer, "qc_f", L)

        params = api_main_text_sand_params_from_qc(qc_for_state)
        Nq = params["Nq"]
        p0_tip = effective_stress_at_depth(layers, L)
        q_unit = Nq * p0_tip

        table_qlim = params["qlim_table"]
        if table_qlim is not None:
            q_unit = min(q_unit, table_qlim)

    else:
        raise ValueError("Method ไม่ถูกต้อง")

    if tip_layer["qlim"] is not None:
        q_unit = min(q_unit, tip_layer["qlim"])

    return q_unit


def end_bearing_cohesive(layer, L):
    cu = layer_value(layer, "cu", L)
    if cu is None:
        return 0.0

    q_unit = 9 * cu

    if layer["qlim"] is not None:
        q_unit = min(q_unit, layer["qlim"])

    return q_unit


def calculate_layer_capacity(D, L, WT, FS, method, layer_lines, loading_type="compression"):
    layers = parse_layer_lines(layer_lines)
    Ap = pile_area(D)
    perimeter = pile_perimeter(D)
    Ar = pile_displacement_ratio(D, WT)

    rows = []
    total_qshaft = 0.0

    for layer in layers:
        z1 = layer["from_depth"]
        z2 = layer["to_depth"]

        if z1 >= L:
            break

        z2_eff = min(z2, L)
        dz = z2_eff - z1

        if dz <= 0:
            continue

        z_mid = 0.5 * (z1 + z2_eff)
        gamma_mid = layer_value(layer, "gamma", z_mid)
        cu_mid = layer_value(layer, "cu", z_mid)
        qc_f_mid = layer_value(layer, "qc_f", z_mid)
        qc_eb_mid = layer_value(layer, "qc_eb", z_mid)

        # Effective stress check values for engineering verification.
        # gamma_eff is effective unit weight at layer mid-depth.
        # p0_layer is the effective stress contribution of this displayed layer.
        # cum_p0 is cumulative effective overburden stress at the bottom of this displayed layer.
        gamma_eff = None
        p0_layer = None
        cum_p0 = None
        if gamma_mid is not None:
            gamma_eff = max(gamma_mid - GAMMA_W, 0.1)
            p0_layer = gamma_eff * dz
            cum_p0 = effective_stress_at_depth(layers, z2_eff)

        unit_shaft, qshaft_layer = integrate_layer_shaft(layer, D, L, WT, layers, method, loading_type)
        total_qshaft += qshaft_layer

        if layer["behavior"] == "cohesive":
            used_parameter = "cu"
        elif method == "API Main Text":
            used_parameter = "Dr(qc), β, Nq"
        else:
            used_parameter = "qc_f"

        rows.append({
            "depth_range": f"{z1:.1f}-{z2_eff:.1f}",
            "soil_type": layer["soil_type"],
            "behavior": layer["behavior"],
            "gamma": gamma_mid,
            "gamma_eff": gamma_eff,
            "p0_layer": p0_layer,
            "cum_p0": cum_p0,
            "cu": cu_mid,
            "qc_f_mpa": qc_f_mid / 1000 if qc_f_mid is not None else None,
            "qc_eb_mpa": qc_eb_mid / 1000 if qc_eb_mid is not None else None,
            "delta_cv": layer["delta_cv"],
            "k0": layer["k0"],
            "flim": layer["flim"],
            "qlim_mpa": layer["qlim"] / 1000 if layer["qlim"] is not None else None,
            "used_parameter": used_parameter,
            "unit_shaft": unit_shaft,
            "qshaft_layer": qshaft_layer,
        })

    qbase = 0.0
    q_unit_base = 0.0
    qc_eb_av = None
    base_model = "Tension: shaft only"

    if loading_type == "compression":
        tip_layer = get_layer_at_depth(layers, L)

        if tip_layer["behavior"] == "cohesive":
            q_unit_base = end_bearing_cohesive(tip_layer, L)
            base_model = "Clay: qbase = 9cu"

        elif tip_layer["behavior"] == "frictional":
            if method == "API Main Text":
                qc_for_state = layer_value(tip_layer, "qc_eb", L)
                if qc_for_state is None:
                    qc_for_state = layer_value(tip_layer, "qc_f", L)

                params = api_main_text_sand_params_from_qc(qc_for_state)
                q_unit_base = end_bearing_frictional(method, qc_for_state, D, WT, layers, L, tip_layer)
                base_model = (
                    "Sand: API Main Text, "
                    f"{params['sand_state']}, "
                    f"Dr={params['Dr_percent']:.1f}%, "
                    f"β={params['beta']:.2f}, "
                    f"Nq={params['Nq']}, "
                    f"flim={params['flim_table']:.0f} kPa, "
                    f"qlim={params['qlim_table'] / 1000:.0f} MPa"
                )
            else:
                qc_eb_av = qc_eb_average_around_tip(layers, L, D)

                if qc_eb_av is None:
                    q_unit_base = 0.0
                    base_model = "No qc_eb near pile tip"
                else:
                    q_unit_base = end_bearing_frictional(method, qc_eb_av, D, WT, layers, L, tip_layer)
                    base_model = f"Frictional: {method} using qc_eb"

            qbase = q_unit_base * Ap

        else:
            qbase = 0.0

        if tip_layer["behavior"] == "cohesive":
            qbase = q_unit_base * Ap

    qult = total_qshaft + qbase
    qallow = qult / FS

    summary = {
        "Ap": Ap,
        "perimeter": perimeter,
        "Ar": Ar,
        "qc_eb_av_1_5D": qc_eb_av,
        "q_unit_base": q_unit_base,
        "Qshaft": total_qshaft,
        "Qbase": qbase,
        "Qult": qult,
        "Qallow": qallow,
        "loading_type": loading_type,
        "base_model": base_model,
    }

    return rows, summary, layers


def calculate_capacity_curve(D, WT, FS, method, layer_lines, loading_type="compression"):
    layers = parse_layer_lines(layer_lines)
    depths = []
    qult = []
    qallow = []
    max_depth = max(layer["to_depth"] for layer in layers)

    current = 5.0
    step = 5.0

    while current <= max_depth:
        try:
            _, summary, _ = calculate_layer_capacity(
                D=D,
                L=current,
                WT=WT,
                FS=FS,
                method=method,
                layer_lines=layer_lines,
                loading_type=loading_type,
            )

            depths.append(current)
            qult.append(summary["Qult"] / 1000)
            qallow.append(summary["Qallow"] / 1000)

        except Exception:
            pass

        current += step

    return depths, qult, qallow