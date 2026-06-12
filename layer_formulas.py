import math

PA = 100.0
DCPT = 0.036


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


def parse_float(value):
    if value == "":
        return None
    return float(value)


def parse_layer_lines(lines):
    layers = []

    for line in lines:
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) != 12:
            raise ValueError(
                "Format ต้องเป็น: from_depth,to_depth,soil_type,behavior,gamma,cu,qc_f,qc_eb,delta_cv,k0,flim,qlim"
            )

        (
            from_depth,
            to_depth,
            soil_type,
            behavior,
            gamma,
            cu,
            qc_f,
            qc_eb,
            delta_cv,
            k0,
            flim,
            qlim
        ) = parts

        layers.append({
            "from_depth": float(from_depth),
            "to_depth": float(to_depth),
            "soil_type": soil_type.lower(),
            "behavior": behavior.lower(),
            "gamma": float(gamma),
            "cu": parse_float(cu),                         # kPa
            "qc_f": parse_float(qc_f) * 1000 if qc_f else None,       # MPa -> kPa
            "qc_eb": parse_float(qc_eb) * 1000 if qc_eb else None,    # MPa -> kPa
            "delta_cv": parse_float(delta_cv),             # degree
            "k0": parse_float(k0),
            "flim": parse_float(flim),                     # kPa
            "qlim": parse_float(qlim) * 1000 if qlim else None        # MPa -> kPa
        })

    layers.sort(key=lambda x: x["from_depth"])
    return layers


def effective_stress_at_depth(layers, z):
    stress = 0.0

    for layer in layers:
        z1 = layer["from_depth"]
        z2 = layer["to_depth"]
        gamma = layer["gamma"]

        if z <= z1:
            continue

        dz = min(z, z2) - z1

        if dz > 0:
            stress += gamma * dz

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


def unit_shaft_cohesive(layer, z_mid, layers):
    cu = layer["cu"]

    if cu is None:
        return 0.0

    p0 = effective_stress_at_depth(layers, z_mid)
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


def unit_shaft_frictional(layer, z_mid, D, L, WT, layers, method, loading_type="compression"):
    qc_f = layer["qc_f"]

    if qc_f is None:
        return 0.0

    Ar = pile_displacement_ratio(D, WT)
    p0 = effective_stress_at_depth(layers, z_mid)

    delta_cv = layer["delta_cv"] if layer["delta_cv"] is not None else 28.8
    tan_delta_cv = math.tan(math.radians(delta_cv))

    if method in ["ICP-05", "UWA-05", "Fugro-05"]:
        p = method_parameters(method, Ar, loading_type)

        term1 = p["u"] * qc_f
        term2 = (p0 / PA) ** p["a"]
        term3 = Ar ** p["b"]
        term4 = max((L - z_mid) / D, p["v"]) ** (-p["c"])
        term5 = tan_delta_cv ** p["d"]
        term6 = min(((L - z_mid) / D) * (1 / p["v"]), 1) ** p["e"]

        unit_shaft = max(term1 * term2 * term3 * term4 * term5 * term6, 0)

    elif method == "NGI-05":
        Dr = relative_density_method4(qc_f, z_mid, layers)
        Fsig = (p0 / PA) ** 0.25
        FDr = 2.1 * (Dr - 0.1) ** 1.7

        if loading_type == "compression":
            unit_shaft = 1.3 * (z_mid / L) * PA * Fsig * FDr
        else:
            unit_shaft = (z_mid / L) * PA * Fsig * FDr

        unit_shaft = max(unit_shaft, 0)

    else:
        raise ValueError("Method ไม่ถูกต้อง")

    if layer["flim"] is not None:
        unit_shaft = min(unit_shaft, layer["flim"])

    return unit_shaft


def relative_density_method4(qc, z, layers):
    p0 = effective_stress_at_depth(layers, z)
    Dr = 0.4 * math.log(qc / (22 * math.sqrt(p0 * PA)))
    return max(Dr, 0.1)


def qc_eb_average_around_tip(layers, L, D):
    z_min = max(0, L - 1.5 * D)
    z_max = L + 1.5 * D

    values = []

    for layer in layers:
        if layer["qc_eb"] is None:
            continue

        overlap = max(
            0,
            min(layer["to_depth"], z_max) - max(layer["from_depth"], z_min)
        )

        if overlap > 0:
            values.append((layer["qc_eb"], overlap))

    if not values:
        return None

    total_weight = sum(w for _, w in values)
    return sum(qc * w for qc, w in values) / total_weight


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
        q_unit = (0.7 * qc_eb_av) / (1 + 3 * Dr**2)

    else:
        raise ValueError("Method ไม่ถูกต้อง")

    if tip_layer["qlim"] is not None:
        q_unit = min(q_unit, tip_layer["qlim"])

    return q_unit


def end_bearing_cohesive(layer):
    cu = layer["cu"]

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

        z_mid = (z1 + z2_eff) / 2

        if layer["behavior"] == "cohesive":
            unit_shaft = unit_shaft_cohesive(layer, z_mid, layers)
            used_parameter = "cu"

        elif layer["behavior"] == "frictional":
            unit_shaft = unit_shaft_frictional(
                layer, z_mid, D, L, WT, layers, method, loading_type
            )
            used_parameter = "qc_f"

        else:
            raise ValueError("behavior ต้องเป็น cohesive หรือ frictional")

        qshaft_layer = unit_shaft * perimeter * dz
        total_qshaft += qshaft_layer

        rows.append({
            "depth_range": f"{z1:.1f}-{z2_eff:.1f}",
            "soil_type": layer["soil_type"],
            "behavior": layer["behavior"],
            "gamma": layer["gamma"],
            "cu": layer["cu"],
            "qc_f_mpa": layer["qc_f"] / 1000 if layer["qc_f"] is not None else None,
            "qc_eb_mpa": layer["qc_eb"] / 1000 if layer["qc_eb"] is not None else None,
            "delta_cv": layer["delta_cv"],
            "k0": layer["k0"],
            "flim": layer["flim"],
            "qlim_mpa": layer["qlim"] / 1000 if layer["qlim"] is not None else None,
            "used_parameter": used_parameter,
            "unit_shaft": unit_shaft,
            "qshaft_layer": qshaft_layer
        })

    qbase = 0.0
    q_unit_base = 0.0
    qc_eb_av = None
    base_model = "Tension: shaft only"

    if loading_type == "compression":
        tip_layer = get_layer_at_depth(layers, L)

        if tip_layer["behavior"] == "cohesive":
            q_unit_base = end_bearing_cohesive(tip_layer)
            base_model = "Clay: qbase = 9cu"

        elif tip_layer["behavior"] == "frictional":
            qc_eb_av = qc_eb_average_around_tip(layers, L, D)

            if qc_eb_av is None:
                q_unit_base = 0.0
                base_model = "No qc_eb near pile tip"
            else:
                q_unit_base = end_bearing_frictional(method, qc_eb_av, D, WT, layers, L, tip_layer)
                base_model = f"Frictional: {method} using qc_eb"

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
        "base_model": base_model
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
                loading_type=loading_type
            )

            depths.append(current)
            qult.append(summary["Qult"] / 1000)
            qallow.append(summary["Qallow"] / 1000)

        except Exception:
            pass

        current += step

    return depths, qult, qallow