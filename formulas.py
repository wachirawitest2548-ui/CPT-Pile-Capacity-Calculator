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
    return 1 - (Di / D) ** 2

def vertical_effective_stress(depth, gamma_eff):
    return max(gamma_eff * depth, 1.0)

def parse_cpt_lines(cpt_lines):
    cpt_data = []
    for line in cpt_lines:
        if not line.strip():
            continue
        depth, qc, soil_type = line.split(",")
        cpt_data.append({
            "depth": float(depth),
            "qc": float(qc),
            "soil_type": soil_type.strip().lower()
        })
    return cpt_data

def qc_average_1_5D(cpt_data, L, D):
    z_min = max(0, L - 1.5 * D)
    z_max = L + 1.5 * D
    values = [row["qc"] for row in cpt_data if z_min <= row["depth"] <= z_max]

    if not values:
        values = [row["qc"] for row in cpt_data if row["depth"] <= L]

    if not values:
        raise ValueError("ไม่มี qc สำหรับคำนวณ qc average")

    return sum(values) / len(values)

def method_parameters(method, Ar):
    if method == "ICP-05":
        return {"a": 0.1, "b": 0.2, "c": 0.4, "d": 1, "e": 0, "u": 0.023, "v": 4 * math.sqrt(Ar)}
    if method == "UWA-05":
        return {"a": 0, "b": 0.3, "c": 0.5, "d": 1, "e": 0, "u": 0.030, "v": 2}
    if method == "Fugro-05":
        return {"a": 0.05, "b": 0.45, "c": 0.90, "d": 0, "e": 1, "u": 0.043, "v": 2 * math.sqrt(Ar)}
    raise ValueError("Method นี้ใช้สูตร Eq.C5 ไม่ได้")

def unit_shaft_eq_c5(qc, z, D, L, WT, gamma_eff, tan_delta_cv, method):
    Ar = pile_displacement_ratio(D, WT)
    p0 = vertical_effective_stress(z, gamma_eff)
    p = method_parameters(method, Ar)

    term1 = p["u"] * qc
    term2 = (p0 / PA) ** p["a"]
    term3 = Ar ** p["b"]
    term4 = max((L - z) / D, p["v"]) ** (-p["c"])
    term5 = tan_delta_cv ** p["d"]
    term6 = min(((L - z) / D) * (1 / p["v"]), 1) ** p["e"]

    return term1 * term2 * term3 * term4 * term5 * term6

def relative_density_method4(qc, z, gamma_eff):
    p0 = vertical_effective_stress(z, gamma_eff)
    Dr = 0.4 * math.log(qc / (22 * math.sqrt(p0 * PA)))
    return max(Dr, 0.1)

def unit_shaft_method4(qc, z, L, gamma_eff):
    p0 = vertical_effective_stress(z, gamma_eff)
    Dr = relative_density_method4(qc, z, gamma_eff)

    Fsig = (p0 / PA) ** 0.25
    FDr = 2.1 * (Dr - 0.1) ** 1.7

    fc = 1.3 * (z / L) * PA * Fsig * FDr
    return max(fc, 0)

def end_bearing(method, qc_av, D, WT, gamma_eff, L):
    Ar = pile_displacement_ratio(D, WT)

    if method == "ICP-05":
        q = qc_av * (0.5 - 0.25 * math.log10(D / DCPT))
        return max(q, 0.15 * qc_av)

    if method == "UWA-05":
        return qc_av * (0.15 + 0.45 * Ar)

    if method == "Fugro-05":
        return 8.5 * PA * (qc_av / PA) ** 0.5 * Ar ** 0.25

    if method == "NGI-05":
        Dr = relative_density_method4(qc_av, L, gamma_eff)
        return (0.7 * qc_av) / (1 + 3 * Dr**2)

    raise ValueError("Method ไม่ถูกต้อง")

def calculate_capacity(D, L, WT, FS, method, gamma_eff, tan_delta_cv, cpt_lines):
    cpt_data = parse_cpt_lines(cpt_lines)

    Ap = pile_area(D)
    perimeter = pile_perimeter(D)
    Ar = pile_displacement_ratio(D, WT)

    rows = []
    total_qshaft = 0
    last_depth = 0

    for row in cpt_data:
        depth = row["depth"]
        qc = row["qc"]
        soil_type = row["soil_type"]

        if depth > L:
            break

        dz = depth - last_depth
        z_mid = (last_depth + depth) / 2

        if soil_type == "sand":
            if method in ["ICP-05", "UWA-05", "Fugro-05"]:
                unit_shaft = unit_shaft_eq_c5(qc, z_mid, D, L, WT, gamma_eff, tan_delta_cv, method)
            elif method == "NGI-05":
                unit_shaft = unit_shaft_method4(qc, z_mid, L, gamma_eff)
            else:
                raise ValueError("Method ไม่ถูกต้อง")

        elif soil_type == "clay":
            unit_shaft = 0.006 * qc

        else:
            raise ValueError("soil_type ต้องเป็น sand หรือ clay")

        qshaft_layer = unit_shaft * perimeter * dz
        total_qshaft += qshaft_layer

        rows.append({
            "depth_range": f"{last_depth:.2f}-{depth:.2f}",
            "dz": dz,
            "qc": qc,
            "soil_type": soil_type,
            "unit_shaft": unit_shaft,
            "qshaft_layer": qshaft_layer
        })

        last_depth = depth

    qc_av = qc_average_1_5D(cpt_data, L, D)
    q_unit_base = end_bearing(method, qc_av, D, WT, gamma_eff, L)
    qbase = q_unit_base * Ap

    qult = total_qshaft + qbase
    qallow = qult / FS

    summary = {
        "Ap": Ap,
        "perimeter": perimeter,
        "Ar": Ar,
        "qc_av_1_5D": qc_av,
        "q_unit_base": q_unit_base,
        "Qshaft": total_qshaft,
        "Qbase": qbase,
        "Qult": qult,
        "Qallow": qallow
    }

    return rows, summary

def calculate_capacity_curve(D, WT, FS, method, gamma_eff, tan_delta_cv, cpt_lines):
    cpt_data = parse_cpt_lines(cpt_lines)

    curve_depths = []
    curve_qult = []
    curve_qallow = []

    for row in cpt_data:
        L_temp = row["depth"]

        try:
            _, summary = calculate_capacity(
                D=D,
                L=L_temp,
                WT=WT,
                FS=FS,
                method=method,
                gamma_eff=gamma_eff,
                tan_delta_cv=tan_delta_cv,
                cpt_lines=cpt_lines
            )

            curve_depths.append(L_temp)
            curve_qult.append(summary["Qult"])
            curve_qallow.append(summary["Qallow"])

        except:
            continue

    return curve_depths, curve_qult, curve_qallow