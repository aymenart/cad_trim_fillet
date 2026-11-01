# SPDX-License-Identifier: GPL-3.0-or-later

# =============================================================================
# CAD TRIM & FILLET — Professional 2D/3D Trimming, Fillet & Chamfer Suite
# Developed by: Aymen Alhaddad (Architect & Developer)
# Copyright (c) 2026 Aymen Alhaddad. All rights reserved.
# =============================================================================
"""CAD Trim & Fillet — Advanced CAD Trimming, Corner Fillet & Chamfer for IngeTrazo.

Features:
- Quick Trim: Click any line segment to erase it between its nearest intersections.
- Boundary Trim: Select a cutting boundary line, then click incoming lines to trim.
- Fillet Arc: Create smooth tangent circular arcs rounding corners between two lines.
  * Supports real-time radius typing in the Measurements box (VCB).
  * Fillet with R = 0 extends or trims to a sharp corner vertex.
  * Real-time rubber-band circular arc preview.
- Chamfer Bevel: Straight-line corner beveled connections with customizable distances.
- Interactive Viewport Tools:
  * Real-time hover preview (spans to be deleted glow in bright red).
  * High-DPI vector icons with automatic dark/light theme adaptation.
  * Dedicated settings dialog for radius, segments, and distances.
  * Full transactional undo/redo integration with IngeTrazo.
  * Multi-language interface (English / Spanish): automatic or chosen in the settings dialog.
"""

from __future__ import annotations

import copy
import math
from typing import List, Tuple, Optional, Any, Dict

from PySide6.QtCore import Qt, QPointF, QSize, QTimer, QLocale, QSettings
from PySide6.QtGui import (
    QVector3D,
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPixmap,
    QIcon,
    QAction,
)
from PySide6.QtWidgets import (
    QApplication,
    QToolBar,
    QMenu,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QComboBox,
)

from tools.base import Tool

KEY = "cad_trim_fillet"
VERSION = "1.0.0"
AUTHOR = "Aymen Alhaddad (Architect & Developer)"
TRANSLATOR = "Fernando Felix"
TITLE = "CAD Trim & Fillet"

TOLERANCE = 1e-4
PARALLEL_EPSILON = 1e-4
COPLANAR_EPSILON = 0.05  # 50 mm tolerance for 3D coplanar intersection

# Global active settings
_SETTINGS = {
    "fillet_radius": 0.50,     # default 0.50 meters
    "fillet_segments": 16,     # arc smoothness
    "chamfer_dist1": 0.30,     # default 0.30 meters
    "chamfer_dist2": 0.30,     # default 0.30 meters
    "trim_tolerance": 0.05,    # 50 mm intersection tolerance
    "language": "auto",        # "auto", "en" or "es" (chosen in the settings dialog)
}

_GLOBAL_APP = None
_ACTIVE_TOOL = None


# =============================================================================
# 0. MULTI-LANGUAGE SUPPORT (ENGLISH / SPANISH)
# =============================================================================
# The user can choose the language in the settings dialog (Automatic / English /
# Spanish). With "Automatic", if IngeTrazo (or the system) uses Spanish the
# interface is shown in Spanish; otherwise in English. The choice is saved
# between sessions. To force a language from the code, set
# FORCE_LANGUAGE = "en" or FORCE_LANGUAGE = "es" (it overrides the dialog).
# To add another language, copy the "en" block inside _TEXTS and translate it.

FORCE_LANGUAGE = None  # None = automatic, "en" = English, "es" = Spanish

_TEXTS: Dict[str, Dict[str, str]] = {
    "en": {
        # --- geometry / operation messages
        "err_zero_vector": "Invalid line: zero length vector.",
        "err_collinear": "collinear",
        "err_parallel": "Lines are parallel.",
        "err_nearly_parallel": "Lines are nearly parallel.",
        "err_non_coplanar": "Non-coplanar (skew: {skew:.1f}mm).",
        "ok_intersection": "Intersection found.",
        "err_zero_length": "One of the lines has zero length.",
        "err_collinear_or_parallel": "Lines are collinear or nearly parallel.",
        "msg_sharp_corner": "Sharp corner",
        "msg_fillet_calc": "Fillet calculated.",
        "msg_chamfer_calc": "Chamfer calculated.",
        "msg_trim_free_line": "Trimmed entire free line segment.",
        "msg_trim_between": "Trimmed line segment between intersections.",
        "err_target_zero": "Target line has zero length.",
        "err_target_no_hit": "Target line does not intersect the boundary cutter.",
        "msg_boundary_trimmed": "Trimmed line against boundary cutter.",
        "msg_extended_sharp": "Extended/trimmed to sharp corner (R=0).",
        "msg_fillet_created": "Fillet created (R={r:.3f}m, {segs} segments).",
        "msg_chamfer_created": "Chamfer created (D1={d1:.3f}m, D2={d2:.3f}m).",
        "msg_trimmed": "Trimmed.",
        "msg_completed": "Completed.",
        # --- status bar messages (tools)
        "trim_start_boundary": "Boundary Trim: Click the CUTTER line first. (Esc = cancel)",
        "trim_start_quick": "Quick Trim: Click any line segment to erase it between intersections. (Esc = cancel)",
        "trim_cancelled": "Trim cancelled.",
        "trim_cutter_selected": "Cutter selected! Now click crossing lines on the side to trim away.",
        "status_next_line": "{msg} (Click next line or Esc to exit)",
        "status_next_segment": "{msg} (Ready for next segment, or Esc to exit)",
        "status_next_line1": "{msg} (Click next Line 1, or Esc to exit)",
        "radius_value": "{v:.3f}m",
        "radius_sharp": "0 (Sharp Corner)",
        "fillet_start": "CAD Fillet [R = {r}]: Click Line 1. (Type radius + Enter to change)",
        "fillet_cancelled": "Fillet cancelled.",
        "radius_negative": "Radius cannot be negative.",
        "radius_updated": "Fillet Radius updated to {r}",
        "fillet_line1_selected": "Line 1 selected! Now click Line 2 to create fillet (R={r:.3f}m).",
        "chamfer_start": "CAD Chamfer [D = {d:.3f}m]: Click Line 1. (Type distance + Enter, Esc = exit)",
        "chamfer_cancelled": "Chamfer cancelled.",
        "distance_positive": "Distance must be greater than zero.",
        "distance_updated": "Chamfer Distance set to {d:.3f}m",
        "chamfer_line1_selected": "Line 1 selected! Now click Line 2 to chamfer (D={d:.3f}m).",
        "vcb_radius": "Radius",
        "vcb_distance": "Distance",
        # --- settings dialog
        "dlg_title": "CAD Trim & Fillet — Settings",
        "dlg_fillet_group": "Fillet Settings",
        "dlg_default_radius": "Default Radius (m):",
        "dlg_arc_segments": "Arc Segments:",
        "dlg_chamfer_group": "Chamfer Settings",
        "dlg_distance1": "Distance 1 (m):",
        "dlg_distance2": "Distance 2 (m):",
        "dlg_save": "Save Settings",
        "dlg_cancel": "Cancel",
        "dlg_language_group": "Language",
        "dlg_language_label": "Interface language:",
        "dlg_lang_auto": "Automatic",
        "dlg_language_note": "Restart IngeTrazo to apply the language to menus and toolbar.",
        "settings_updated": "CAD Trim & Fillet settings updated.",
        # --- toolbar / menus
        "tool_label_prefix": "Tool: {name}",
        "tool_label_trim_quick": "CAD Trim (Quick)",
        "tool_label_trim_boundary": "CAD Trim (Boundary)",
        "tool_label_fillet": "CAD Fillet",
        "tool_label_chamfer": "CAD Chamfer",
        "act_quick_title": "Quick Trim",
        "act_quick_tip": "Click any line segment to erase it between bounding intersections.",
        "act_boundary_title": "Boundary Trim",
        "act_boundary_tip": "Click cutting boundary first, then click lines to trim.",
        "act_fillet_title": "Fillet Arc",
        "act_fillet_tip": "Create smooth tangent circular arc rounding corner (supports typing radius in VCB).",
        "act_chamfer_title": "Chamfer Bevel",
        "act_chamfer_tip": "Create straight beveled corner between two lines (supports typing distance in VCB).",
        "act_settings_title": "Settings...",
        "act_settings_tip": "Configure Fillet Radius, Arc Segments, and Chamfer Distances.",
        "author_line": "Author: {a}",
        "translator_line": "Spanish translation: {t}",
    },
    "es": {
        # --- geometry / operation messages
        "err_zero_vector": "Línea no válida: vector de longitud cero.",
        "err_collinear": "Las líneas son colineales.",
        "err_parallel": "Las líneas son paralelas.",
        "err_nearly_parallel": "Las líneas son casi paralelas.",
        "err_non_coplanar": "No coplanares (desviación: {skew:.1f} mm).",
        "ok_intersection": "Intersección encontrada.",
        "err_zero_length": "Una de las líneas tiene longitud cero.",
        "err_collinear_or_parallel": "Las líneas son colineales o casi paralelas.",
        "msg_sharp_corner": "Esquina viva",
        "msg_fillet_calc": "Empalme calculado.",
        "msg_chamfer_calc": "Chaflán calculado.",
        "msg_trim_free_line": "Se recortó todo el segmento de línea libre.",
        "msg_trim_between": "Segmento de línea recortado entre intersecciones.",
        "err_target_zero": "La línea de destino tiene longitud cero.",
        "err_target_no_hit": "La línea de destino no corta con el límite de corte.",
        "msg_boundary_trimmed": "Línea recortada contra el límite de corte.",
        "msg_extended_sharp": "Extendida/recortada hasta esquina viva (R=0).",
        "msg_fillet_created": "Empalme creado (R={r:.3f} m, {segs} segmentos).",
        "msg_chamfer_created": "Chaflán creado (D1={d1:.3f} m, D2={d2:.3f} m).",
        "msg_trimmed": "Recortado.",
        "msg_completed": "Completado.",
        # --- status bar messages (tools)
        "trim_start_boundary": "Recorte por límite: haz clic primero en la línea de CORTE. (Esc = cancelar)",
        "trim_start_quick": "Recorte rápido: haz clic en cualquier segmento de línea para borrarlo entre intersecciones. (Esc = cancelar)",
        "trim_cancelled": "Recorte cancelado.",
        "trim_cutter_selected": "¡Línea de corte seleccionada! Ahora haz clic en las líneas que la cruzan, en el lado que quieres recortar.",
        "status_next_line": "{msg} (Haz clic en la siguiente línea o Esc para salir)",
        "status_next_segment": "{msg} (Listo para el siguiente segmento, o Esc para salir)",
        "status_next_line1": "{msg} (Haz clic en la siguiente línea 1, o Esc para salir)",
        "radius_value": "{v:.3f} m",
        "radius_sharp": "0 (esquina viva)",
        "fillet_start": "CAD Empalme [R = {r}]: haz clic en la línea 1. (Escribe el radio + Enter para cambiarlo)",
        "fillet_cancelled": "Empalme cancelado.",
        "radius_negative": "El radio no puede ser negativo.",
        "radius_updated": "Radio de empalme actualizado a {r}",
        "fillet_line1_selected": "¡Línea 1 seleccionada! Ahora haz clic en la línea 2 para crear el empalme (R={r:.3f} m).",
        "chamfer_start": "CAD Chaflán [D = {d:.3f} m]: haz clic en la línea 1. (Escribe la distancia + Enter, Esc = salir)",
        "chamfer_cancelled": "Chaflán cancelado.",
        "distance_positive": "La distancia debe ser mayor que cero.",
        "distance_updated": "Distancia de chaflán establecida en {d:.3f} m",
        "chamfer_line1_selected": "¡Línea 1 seleccionada! Ahora haz clic en la línea 2 para aplicar el chaflán (D={d:.3f} m).",
        "vcb_radius": "Radio",
        "vcb_distance": "Distancia",
        # --- settings dialog
        "dlg_title": "CAD Trim & Fillet — Configuración",
        "dlg_fillet_group": "Configuración de empalme",
        "dlg_default_radius": "Radio predeterminado (m):",
        "dlg_arc_segments": "Segmentos del arco:",
        "dlg_chamfer_group": "Configuración de chaflán",
        "dlg_distance1": "Distancia 1 (m):",
        "dlg_distance2": "Distancia 2 (m):",
        "dlg_save": "Guardar configuración",
        "dlg_cancel": "Cancelar",
        "dlg_language_group": "Idioma",
        "dlg_language_label": "Idioma de la interfaz:",
        "dlg_lang_auto": "Automático",
        "dlg_language_note": "Reinicia IngeTrazo para aplicar el idioma en los menús y la barra de herramientas.",
        "settings_updated": "Configuración de CAD Trim & Fillet actualizada.",
        # --- toolbar / menus
        "tool_label_prefix": "Herramienta: {name}",
        "tool_label_trim_quick": "CAD Recorte rápido",
        "tool_label_trim_boundary": "CAD Recorte por límite",
        "tool_label_fillet": "CAD Empalme",
        "tool_label_chamfer": "CAD Chaflán",
        "act_quick_title": "Recorte rápido",
        "act_quick_tip": "Haz clic en cualquier segmento de línea para borrarlo entre las intersecciones que lo delimitan.",
        "act_boundary_title": "Recorte por límite",
        "act_boundary_tip": "Haz clic primero en el límite de corte y luego en las líneas que quieres recortar.",
        "act_fillet_title": "Arco de empalme",
        "act_fillet_tip": "Crea un arco circular tangente que redondea la esquina (permite escribir el radio en el cuadro de medidas).",
        "act_chamfer_title": "Chaflán",
        "act_chamfer_tip": "Crea un chaflán recto entre dos líneas (permite escribir la distancia en el cuadro de medidas).",
        "act_settings_title": "Configuración...",
        "act_settings_tip": "Configura el radio de empalme, los segmentos del arco y las distancias del chaflán.",
        "author_line": "Autor: {a}",
        "translator_line": "Traducción al español: {t}",
    },
}


def current_language() -> str:
    """Return "es" or "en" depending on FORCE_LANGUAGE, IngeTrazo or the system."""
    if FORCE_LANGUAGE in ("en", "es"):
        return FORCE_LANGUAGE

    chosen = _SETTINGS.get("language", "auto")
    if chosen in ("en", "es"):
        return chosen

    candidates: List[str] = []
    app = _GLOBAL_APP
    if app is not None:
        for attr in ("language", "lang", "locale"):
            val = getattr(app, attr, None)
            if isinstance(val, str):
                candidates.append(val)
    try:
        name = QLocale().name()
        if isinstance(name, str):
            candidates.append(name)
    except Exception:
        pass

    for code in candidates:
        code = code.strip().lower()
        if code.startswith("es"):
            return "es"
        if code.startswith("en"):
            return "en"
    return "en"


def tr(key: str, **kwargs: Any) -> str:
    """Translate a text key into the active language (falls back to English)."""
    texts = _TEXTS.get(current_language(), _TEXTS["en"])
    text = texts.get(key)
    if text is None:
        text = _TEXTS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def _credits_html() -> str:
    """Author (and Spanish translator) lines for button tooltips."""
    html = "<br><i>" + tr("author_line", a=AUTHOR) + "</i>"
    if current_language() == "es":
        html += "<br><i>" + tr("translator_line", t=TRANSLATOR) + "</i>"
    return html


_SETTINGS_ORG = "IngeTrazo"
_SETTINGS_APP = "cad_trim_fillet"


def _load_saved_language() -> str:
    """Read the language chosen in the settings dialog (kept between sessions)."""
    try:
        value = QSettings(_SETTINGS_ORG, _SETTINGS_APP).value("language", "auto")
        if isinstance(value, str) and value in ("auto", "en", "es"):
            return value
    except Exception:
        pass
    return "auto"


def save_language_preference(value: str) -> None:
    """Remember the chosen language ("auto", "en" or "es")."""
    if value not in ("auto", "en", "es"):
        value = "auto"
    _SETTINGS["language"] = value
    try:
        QSettings(_SETTINGS_ORG, _SETTINGS_APP).setValue("language", value)
    except Exception:
        pass


_SETTINGS["language"] = _load_saved_language()


# =============================================================================
# 1. 3D VECTOR & CAD GEOMETRIC ENGINE
# =============================================================================

def to_v3d(v: Any) -> QVector3D:
    """Safely convert any vector or coordinate tuple to a PySide6 QVector3D."""
    if isinstance(v, QVector3D):
        return QVector3D(v.x(), v.y(), v.z())
    if hasattr(v, "x") and hasattr(v, "y") and hasattr(v, "z"):
        return QVector3D(float(v.x()), float(v.y()), float(v.z()))
    if isinstance(v, (tuple, list)) and len(v) >= 3:
        return QVector3D(float(v[0]), float(v[1]), float(v[2]))
    return QVector3D(v)


def distance_3d(p1: Any, p2: Any) -> float:
    """Euclidean distance between two 3D points."""
    return (to_v3d(p1) - to_v3d(p2)).length()


def rotate_vector_3d(v: QVector3D, axis: QVector3D, angle_rad: float) -> QVector3D:
    """Rotate 3D vector around an arbitrary axis using Rodrigues' rotation formula."""
    k = axis.normalized()
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return (
        v * cos_a
        + QVector3D.crossProduct(k, v) * sin_a
        + k * QVector3D.dotProduct(k, v) * (1.0 - cos_a)
    )


def intersect_lines_3d_detailed(
    p1: QVector3D, v1: QVector3D, p2: QVector3D, v2: QVector3D, coplanar_tol: float = COPLANAR_EPSILON
) -> Tuple[bool, Optional[QVector3D], str, Tuple[float, float]]:
    """Calculate the 3D closest approach / intersection of two infinite lines.

    Lines: L1(t) = p1 + t * dir1, L2(u) = p2 + u * dir2
    Returns: (success, intersection_pt, msg, (t, u))
    """
    v1_len = v1.length()
    v2_len = v2.length()
    if v1_len < 1e-7 or v2_len < 1e-7:
        return False, None, tr("err_zero_vector"), (0.0, 0.0)

    dir1 = v1 / v1_len
    dir2 = v2 / v2_len

    cross_dir = QVector3D.crossProduct(dir1, dir2)
    cross_len = cross_dir.length()
    delta_p = p2 - p1

    if cross_len < PARALLEL_EPSILON:
        collinear_dist = QVector3D.crossProduct(delta_p, dir1).length()
        if collinear_dist < 1e-3:
            return True, None, tr("err_collinear"), (0.0, 0.0)
        return False, None, tr("err_parallel"), (0.0, 0.0)

    b = QVector3D.dotProduct(dir1, dir2)
    d = QVector3D.dotProduct(dir1, delta_p)
    e = QVector3D.dotProduct(dir2, delta_p)

    denom = 1.0 - (b * b)
    if abs(denom) < 1e-7:
        return False, None, tr("err_nearly_parallel"), (0.0, 0.0)

    t = (d - b * e) / denom
    u = (b * d - e) / denom

    pt1 = p1 + dir1 * t
    pt2 = p2 + dir2 * u

    skew_dist = (pt2 - pt1).length()
    if skew_dist > coplanar_tol:
        return False, None, tr("err_non_coplanar", skew=skew_dist * 1000), (t, u)

    intersection_pt = (pt1 + pt2) * 0.5
    return True, intersection_pt, tr("ok_intersection"), (t, u)


def intersect_segments_3d(
    pA0: QVector3D, pA1: QVector3D, pB0: QVector3D, pB1: QVector3D, tol: float = COPLANAR_EPSILON
) -> Tuple[bool, Optional[QVector3D], float, float]:
    """Check if two finite 3D segments intersect within their lengths.

    Returns: (intersects, intersection_pt, t, u)
    """
    v1 = pA1 - pA0
    v2 = pB1 - pB0
    L1 = v1.length()
    L2 = v2.length()
    if L1 < 1e-6 or L2 < 1e-6:
        return False, None, 0.0, 0.0

    ok, int_pt, _, (t, u) = intersect_lines_3d_detailed(pA0, v1, pB0, v2, tol)
    if not ok or int_pt is None:
        return False, None, 0.0, 0.0

    # Ensure intersection point lies strictly inside both segments
    if 0.001 <= t <= L1 - 0.001 and 0.001 <= u <= L2 - 0.001:
        return True, int_pt, t, u

    return False, None, 0.0, 0.0


# =============================================================================
# 2. MESH MUTATION & TOPOLOGY HELPERS
# =============================================================================

def mark_mesh_modified(mesh, scene=None) -> None:
    """Mark mesh as modified to trigger immediate viewport redraw."""
    if hasattr(mesh, "_chunk_dirty"):
        mesh._chunk_dirty = True
    if hasattr(mesh, "_mut_serial"):
        mesh._mut_serial += 1
    if scene and hasattr(scene, "version"):
        scene.version += 1


def pick_edge_at(viewport, x: float, y: float) -> Optional[Any]:
    """Pick visible edge under screen coordinates."""
    ix, iy = int(round(x)), int(round(y))
    pick = getattr(viewport, "pick_visible_edge", None) or getattr(viewport, "pick_edge", None)
    if callable(pick):
        try:
            edge = pick(ix, iy)
            from core.mesh import Edge
            if isinstance(edge, Edge):
                return edge
        except Exception:
            pass
    return None


def split_edge_safe(mesh, edge: Any, split_pt: QVector3D) -> Tuple[Optional[Any], Optional[Any]]:
    """Safely split an edge into two sub-edges at split_pt."""
    p0 = to_v3d(edge.v0.position)
    p1 = to_v3d(edge.v1.position)
    s_pt = to_v3d(split_pt)

    if (p0 - s_pt).length() < 1e-4 or (p1 - s_pt).length() < 1e-4:
        return edge, None

    if hasattr(mesh, "split_edge"):
        try:
            return mesh.split_edge(edge, s_pt)
        except Exception:
            pass

    curve_id = getattr(edge, "curve", None)
    if hasattr(mesh, "remove_edge"):
        try:
            mesh.remove_edge(edge)
        except Exception:
            pass

    e1 = mesh.add_edge(p0, s_pt)
    e2 = mesh.add_edge(s_pt, p1)

    if curve_id is not None:
        if hasattr(e1, "curve"): e1.curve = curve_id
        if hasattr(e2, "curve"): e2.curve = curve_id

    return e1, e2


def find_all_intersections_on_edge(
    mesh, target_edge: Any, tol: float = COPLANAR_EPSILON
) -> List[Tuple[float, QVector3D]]:
    """Find all intersections along target_edge with other mesh edges.

    Returns sorted list of (t, intersection_pt) along the edge.
    """
    pA0 = to_v3d(target_edge.v0.position)
    pA1 = to_v3d(target_edge.v1.position)
    vA = pA1 - pA0
    LA = vA.length()
    if LA < 1e-6:
        return []

    hits: List[Tuple[float, QVector3D]] = []

    for other in mesh.edges:
        if other is target_edge:
            continue
        pB0 = to_v3d(other.v0.position)
        pB1 = to_v3d(other.v1.position)

        ok, int_pt, t, u = intersect_segments_3d(pA0, pA1, pB0, pB1, tol)
        if ok and int_pt is not None:
            # Check for duplicate intersection parameter
            if not any(abs(t - existing[0]) < 1e-3 for existing in hits):
                hits.append((t, int_pt))

    hits.sort(key=lambda item: item[0])
    return hits


def find_trim_span(
    target_edge: Any, intersections: List[Tuple[float, QVector3D]], click_pt: QVector3D
) -> Tuple[QVector3D, QVector3D, float, float]:
    """Find the start and end 3D points of the segment span containing click_pt."""
    pA0 = to_v3d(target_edge.v0.position)
    pA1 = to_v3d(target_edge.v1.position)
    vA = pA1 - pA0
    LA = vA.length()
    dA = vA / LA if LA > 1e-6 else QVector3D(0, 0, 0)

    # Click parameter along edge
    t_click = QVector3D.dotProduct(click_pt - pA0, dA)
    t_click = max(0.0, min(LA, t_click))

    # All division parameters along the edge
    params = [0.0] + [item[0] for item in intersections] + [LA]
    pts = [pA0] + [item[1] for item in intersections] + [pA1]

    # Locate which interval [params[i], params[i+1]] contains t_click
    for i in range(len(params) - 1):
        t_start = params[i]
        t_end = params[i + 1]
        if t_start - 1e-4 <= t_click <= t_end + 1e-4:
            return pts[i], pts[i + 1], t_start, t_end

    return pA0, pA1, 0.0, LA


# =============================================================================
# 3. FILLET & CHAMFER GEOMETRY COMPUTATION
# =============================================================================

def compute_fillet_geometry(
    edge1: Any, edge2: Any, radius: float,
    click1: Optional[QVector3D] = None, click2: Optional[QVector3D] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """Compute the exact tangent circular arc, tangent points, and trimmed legs."""
    pA0 = to_v3d(edge1.v0.position)
    pA1 = to_v3d(edge1.v1.position)
    pB0 = to_v3d(edge2.v0.position)
    pB1 = to_v3d(edge2.v1.position)

    v1_full = pA1 - pA0
    v2_full = pB1 - pB0
    L1 = v1_full.length()
    L2 = v2_full.length()
    if L1 < 1e-6 or L2 < 1e-6:
        return False, tr("err_zero_length"), {}

    d1 = v1_full / L1
    d2 = v2_full / L2

    ok, V, msg, (t, u) = intersect_lines_3d_detailed(pA0, d1, pB0, d2)
    if not ok or V is None:
        return False, msg, {}

    # Direction away from V along Line 1
    # Use click position to keep the portion the user clicked
    if click1 is not None and (click1 - V).length() > 1e-4:
        c_dir1 = (click1 - V).normalized()
        u1 = d1 if QVector3D.dotProduct(d1, c_dir1) > 0 else -d1
        pA_far = pA1 if QVector3D.dotProduct(d1, c_dir1) > 0 else pA0
    else:
        # Default: point into the longer side of the segment from V
        if (pA1 - V).length() > (pA0 - V).length():
            u1 = (pA1 - V).normalized()
            pA_far = pA1
        else:
            u1 = (pA0 - V).normalized()
            pA_far = pA0

    # Direction away from V along Line 2
    if click2 is not None and (click2 - V).length() > 1e-4:
        c_dir2 = (click2 - V).normalized()
        u2 = d2 if QVector3D.dotProduct(d2, c_dir2) > 0 else -d2
        pB_far = pB1 if QVector3D.dotProduct(d2, c_dir2) > 0 else pB0
    else:
        if (pB1 - V).length() > (pB0 - V).length():
            u2 = (pB1 - V).normalized()
            pB_far = pB1
        else:
            u2 = (pB0 - V).normalized()
            pB_far = pB0

    cos_theta = max(-1.0, min(1.0, float(QVector3D.dotProduct(u1, u2))))
    theta = math.acos(cos_theta)
    if theta < 0.02 or theta > math.pi - 0.02:
        return False, tr("err_collinear_or_parallel"), {}

    tan_half = math.tan(theta * 0.5)
    sin_half = math.sin(theta * 0.5)

    if radius < 1e-4:
        # Sharp corner (R = 0)
        return True, tr("msg_sharp_corner"), {
            "V": V, "T1": V, "T2": V, "C": V, "pA_far": pA_far, "pB_far": pB_far,
            "arc_points": [], "is_sharp": True, "radius": 0.0
        }

    d_tan = radius / tan_half
    h_cen = radius / sin_half

    T1 = V + u1 * d_tan
    T2 = V + u2 * d_tan
    bisector = (u1 + u2).normalized()
    C = V + bisector * h_cen

    r1 = T1 - C
    r2 = T2 - C
    rot_axis = QVector3D.crossProduct(r1, r2).normalized()

    cos_phi = max(-1.0, min(1.0, float(QVector3D.dotProduct(r1.normalized(), r2.normalized()))))
    phi = math.acos(cos_phi)

    # Arc points
    n_segs = max(4, _SETTINGS.get("fillet_segments", 16))
    arc_points = []
    for k in range(n_segs + 1):
        ang = phi * k / n_segs
        pt = C + rotate_vector_3d(r1, rot_axis, ang)
        arc_points.append(pt)

    return True, tr("msg_fillet_calc"), {
        "V": V, "T1": T1, "T2": T2, "C": C, "pA_far": pA_far, "pB_far": pB_far,
        "arc_points": arc_points, "is_sharp": False, "radius": radius,
        "d_tan": d_tan, "theta": theta
    }


def compute_chamfer_geometry(
    edge1: Any, edge2: Any, dist1: float, dist2: float,
    click1: Optional[QVector3D] = None, click2: Optional[QVector3D] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """Compute straight chamfer bevel between two lines."""
    pA0 = to_v3d(edge1.v0.position)
    pA1 = to_v3d(edge1.v1.position)
    pB0 = to_v3d(edge2.v0.position)
    pB1 = to_v3d(edge2.v1.position)

    v1_full = pA1 - pA0
    v2_full = pB1 - pB0
    L1 = v1_full.length()
    L2 = v2_full.length()
    if L1 < 1e-6 or L2 < 1e-6:
        return False, tr("err_zero_length"), {}

    d1 = v1_full / L1
    d2 = v2_full / L2

    ok, V, msg, _ = intersect_lines_3d_detailed(pA0, d1, pB0, d2)
    if not ok or V is None:
        return False, msg, {}

    if click1 is not None and (click1 - V).length() > 1e-4:
        c_dir1 = (click1 - V).normalized()
        u1 = d1 if QVector3D.dotProduct(d1, c_dir1) > 0 else -d1
        pA_far = pA1 if QVector3D.dotProduct(d1, c_dir1) > 0 else pA0
    else:
        if (pA1 - V).length() > (pA0 - V).length():
            u1 = (pA1 - V).normalized()
            pA_far = pA1
        else:
            u1 = (pA0 - V).normalized()
            pA_far = pA0

    if click2 is not None and (click2 - V).length() > 1e-4:
        c_dir2 = (click2 - V).normalized()
        u2 = d2 if QVector3D.dotProduct(d2, c_dir2) > 0 else -d2
        pB_far = pB1 if QVector3D.dotProduct(d2, c_dir2) > 0 else pB0
    else:
        if (pB1 - V).length() > (pB0 - V).length():
            u2 = (pB1 - V).normalized()
            pB_far = pB1
        else:
            u2 = (pB0 - V).normalized()
            pB_far = pB0

    T1 = V + u1 * dist1
    T2 = V + u2 * dist2

    return True, tr("msg_chamfer_calc"), {
        "V": V, "T1": T1, "T2": T2, "pA_far": pA_far, "pB_far": pB_far
    }


# =============================================================================
# 4. CORE CAD MUTATION OPERATORS & B-REP FACE CORNER HEALER
# =============================================================================

def update_mesh_corner(
    mesh: Any,
    edge1: Any,
    edge2: Any,
    V: QVector3D,
    T1: QVector3D,
    T2: QVector3D,
    pA_far: QVector3D,
    pB_far: QVector3D,
    arc_points: List[QVector3D],
    is_sharp: bool = False,
) -> None:
    """Update corner geometry for both wireframe edges and incident B-Rep faces.

    Replaces the sharp corner V with the tangent arc (or chamfer segment) in
    all incident faces, removing the outer surface wedge outside the cut.
    """
    # 1. Identify all faces attached to edge1, edge2, or corner vertex V
    affected_faces = set()
    if hasattr(edge1, "faces") and edge1.faces:
        for f in edge1.faces:
            if f in mesh.faces:
                affected_faces.add(f)
    if hasattr(edge2, "faces") and edge2.faces:
        for f in edge2.faces:
            if f in mesh.faces:
                affected_faces.add(f)

    # Also inspect mesh.faces for any face having a corner at V connected to edge1/edge2
    for f in list(mesh.faces):
        if f not in affected_faces and hasattr(f, "loop"):
            has_v = any((to_v3d(v.position) - V).length() < 0.02 for v in f.loop)
            if has_v:
                e1_pts = [to_v3d(edge1.v0.position), to_v3d(edge1.v1.position)]
                e2_pts = [to_v3d(edge2.v0.position), to_v3d(edge2.v1.position)]
                f_pts = [to_v3d(v.position) for v in f.loop]
                shares_e1 = any(any((fp - ep).length() < 0.02 for ep in e1_pts) for fp in f_pts)
                shares_e2 = any(any((fp - ep).length() < 0.02 for ep in e2_pts) for fp in f_pts)
                if shares_e1 or shares_e2:
                    affected_faces.add(f)

    # 2. Replacement points for corner V
    if is_sharp:
        pts_1_to_2 = [V]
        pts_2_to_1 = [V]
    elif arc_points:
        pts_1_to_2 = arc_points
        pts_2_to_1 = list(reversed(arc_points))
    else:
        # Chamfer (straight bevel)
        pts_1_to_2 = [T1, T2]
        pts_2_to_1 = [T2, T1]

    face_reconstructions = []
    for face in affected_faces:
        outer_pts = [to_v3d(v.position) for v in face.loop]
        n = len(outer_pts)
        if n < 3:
            continue

        best_idx = -1
        min_dist = float("inf")
        for i, pt in enumerate(outer_pts):
            d = (pt - V).length()
            if d < min_dist:
                min_dist = d
                best_idx = i

        new_outer = None
        if min_dist <= 0.05:
            prev_pt = outer_pts[(best_idx - 1) % n]
            next_pt = outer_pts[(best_idx + 1) % n]

            cost_12 = (prev_pt - T1).length() + (next_pt - T2).length()
            cost_21 = (prev_pt - T2).length() + (next_pt - T1).length()

            rep = pts_1_to_2 if cost_12 <= cost_21 else pts_2_to_1
            raw_new = outer_pts[:best_idx] + rep + outer_pts[best_idx + 1:]

            clean_new = []
            for p in raw_new:
                if not clean_new or (p - clean_new[-1]).length() > 1e-4:
                    clean_new.append(p)
            if len(clean_new) > 1 and (clean_new[0] - clean_new[-1]).length() < 1e-4:
                clean_new.pop()

            if len(clean_new) >= 3:
                new_outer = clean_new

        # Check hole loops if any
        new_holes = []
        for h in getattr(face, "hole_loops", []):
            h_pts = [to_v3d(v.position) for v in h]
            hn = len(h_pts)
            h_best = -1
            h_min = float("inf")
            for i, pt in enumerate(h_pts):
                d = (pt - V).length()
                if d < h_min:
                    h_min = d
                    h_best = i

            if h_min <= 0.05 and hn >= 3:
                h_prev = h_pts[(h_best - 1) % hn]
                h_next = h_pts[(h_best + 1) % hn]
                c12 = (h_prev - T1).length() + (h_next - T2).length()
                c21 = (h_prev - T2).length() + (h_next - T1).length()
                h_rep = pts_1_to_2 if c12 <= c21 else pts_2_to_1
                h_raw = h_pts[:h_best] + h_rep + h_pts[h_best + 1:]
                h_clean = []
                for p in h_raw:
                    if not h_clean or (p - h_clean[-1]).length() > 1e-4:
                        h_clean.append(p)
                if len(h_clean) > 1 and (h_clean[0] - h_clean[-1]).length() < 1e-4:
                    h_clean.pop()
                if len(h_clean) >= 3:
                    new_holes.append(h_clean)
            else:
                new_holes.append(h_pts)

        if new_outer is not None:
            face_reconstructions.append({
                "face": face,
                "loop": new_outer,
                "holes": new_holes,
                "attrs": copy.deepcopy(getattr(face, "attrs", {})),
                "interior": getattr(face, "interior", False),
            })

    # 3. Remove old faces first so their topology doesn't conflict
    for item in face_reconstructions:
        if hasattr(mesh, "remove_face") and item["face"] in mesh.faces:
            mesh.remove_face(item["face"])

    # 4. Remove old corner edges
    if hasattr(mesh, "remove_edge"):
        if edge1 in mesh.edges:
            mesh.remove_edge(edge1)
        if edge2 in mesh.edges:
            mesh.remove_edge(edge2)

    # 5. Add trimmed straight legs
    if (pA_far - T1).length() > 1e-4:
        mesh.add_edge(pA_far, T1)
    if (pB_far - T2).length() > 1e-4:
        mesh.add_edge(pB_far, T2)

    # 6. Add smooth tangent arc edges (or chamfer straight edge)
    if arc_points:
        curve_id = getattr(mesh, "next_curve_id", None)
        cid = curve_id() if callable(curve_id) else None
        for i in range(len(arc_points) - 1):
            arc_e = mesh.add_edge(arc_points[i], arc_points[i + 1])
            if cid is not None and hasattr(arc_e, "curve"):
                arc_e.curve = cid
    elif not is_sharp:
        # Chamfer edge
        mesh.add_edge(T1, T2)
    elif is_sharp:
        if (pA_far - V).length() > 1e-4:
            mesh.add_edge(pA_far, V)
        if (pB_far - V).length() > 1e-4:
            mesh.add_edge(pB_far, V)

    # 7. Add reconstructed faces (perfectly trimmed to arc / chamfer boundary)
    for item in face_reconstructions:
        try:
            if item["holes"]:
                new_f = mesh.add_face(item["loop"], item["holes"])
            else:
                new_f = mesh.add_face(item["loop"])
            if item["attrs"] and hasattr(new_f, "attrs"):
                new_f.attrs = item["attrs"]
            if hasattr(new_f, "interior"):
                new_f.interior = item["interior"]
        except Exception:
            pass

    # 8. Clean up coincidences and orphan vertices
    if hasattr(mesh, "weld_coincident"):
        mesh.weld_coincident()
    if hasattr(mesh, "prune_orphan_vertices"):
        mesh.prune_orphan_vertices()

    mark_mesh_modified(mesh)


def op_quick_trim(mesh, target_edge: Any, click_pt: QVector3D) -> Tuple[bool, str]:
    """Quick Trim: erase the exact segment span under click_pt between bounding intersections."""
    intersections = find_all_intersections_on_edge(mesh, target_edge, _SETTINGS["trim_tolerance"])
    pA0 = to_v3d(target_edge.v0.position)
    pA1 = to_v3d(target_edge.v1.position)

    # Remove any broken faces referencing target_edge
    if hasattr(target_edge, "faces") and target_edge.faces:
        for f in list(target_edge.faces):
            if hasattr(mesh, "remove_face") and f in mesh.faces:
                mesh.remove_face(f)

    if not intersections:
        # No intersections along this edge: delete entire edge
        if hasattr(mesh, "remove_edge"):
            mesh.remove_edge(target_edge)
        if hasattr(mesh, "prune_orphan_vertices"):
            mesh.prune_orphan_vertices()
        mark_mesh_modified(mesh)
        return True, tr("msg_trim_free_line")

    s_pt, e_pt, t_start, t_end = find_trim_span(target_edge, intersections, click_pt)

    # 1. Collect all points to split: s_pt and e_pt (if not already endpoints)
    points_to_insert = []
    if (s_pt - pA0).length() > 1e-3 and (s_pt - pA1).length() > 1e-3:
        points_to_insert.append(s_pt)
    if (e_pt - pA0).length() > 1e-3 and (e_pt - pA1).length() > 1e-3:
        points_to_insert.append(e_pt)

    # 2. Divide edge into pieces
    # Remove original target edge
    if hasattr(mesh, "remove_edge"):
        mesh.remove_edge(target_edge)

    # All chain parameters
    LA = (pA1 - pA0).length()
    dA = (pA1 - pA0) / LA
    chain_pts = [pA0] + [item[1] for item in intersections] + [pA1]

    # Add back all sub-edges EXCEPT the span between s_pt and e_pt!
    for i in range(len(chain_pts) - 1):
        pt_a = chain_pts[i]
        pt_b = chain_pts[i + 1]
        mid = (pt_a + pt_b) * 0.5
        t_mid = QVector3D.dotProduct(mid - pA0, dA)

        # Skip the span that was clicked!
        if t_start - 1e-4 <= t_mid <= t_end + 1e-4:
            continue

        mesh.add_edge(pt_a, pt_b)

    if hasattr(mesh, "weld_coincident"):
        mesh.weld_coincident()
    if hasattr(mesh, "prune_orphan_vertices"):
        mesh.prune_orphan_vertices()

    mark_mesh_modified(mesh)
    return True, tr("msg_trim_between")


def op_boundary_trim(
    mesh, cutter_edge: Any, target_edge: Any, click_pt: QVector3D
) -> Tuple[bool, str]:
    """Boundary Trim: trim target_edge against cutter_edge, removing the clicked side."""
    pC0 = to_v3d(cutter_edge.v0.position)
    pC1 = to_v3d(cutter_edge.v1.position)
    pT0 = to_v3d(target_edge.v0.position)
    pT1 = to_v3d(target_edge.v1.position)

    vT = pT1 - pT0
    LT = vT.length()
    if LT < 1e-6:
        return False, tr("err_target_zero")

    ok, int_pt, msg, (t, u) = intersect_lines_3d_detailed(pT0, vT, pC0, pC1 - pC0)
    if not ok or int_pt is None:
        return False, tr("err_target_no_hit")

    dT = vT / LT
    t_click = QVector3D.dotProduct(click_pt - pT0, dT)

    # Remove any broken faces referencing target_edge
    if hasattr(target_edge, "faces") and target_edge.faces:
        for f in list(target_edge.faces):
            if hasattr(mesh, "remove_face") and f in mesh.faces:
                mesh.remove_face(f)

    # Remove target edge
    if hasattr(mesh, "remove_edge"):
        mesh.remove_edge(target_edge)

    # Keep the side OPPOSITE to the click
    if t_click > t:
        # Clicked side was towards pT1 -> keep [pT0, int_pt]
        if (pT0 - int_pt).length() > 1e-3:
            mesh.add_edge(pT0, int_pt)
    else:
        # Clicked side was towards pT0 -> keep [int_pt, pT1]
        if (pT1 - int_pt).length() > 1e-3:
            mesh.add_edge(int_pt, pT1)

    # Split cutter edge at int_pt if int_pt lies inside cutter
    LC = (pC1 - pC0).length()
    if 0.001 <= u <= LC - 0.001:
        split_edge_safe(mesh, cutter_edge, int_pt)

    if hasattr(mesh, "weld_coincident"):
        mesh.weld_coincident()
    if hasattr(mesh, "prune_orphan_vertices"):
        mesh.prune_orphan_vertices()

    mark_mesh_modified(mesh)
    return True, tr("msg_boundary_trimmed")


def op_fillet(
    mesh, edge1: Any, edge2: Any, radius: float, segments: int = 16,
    click1: Optional[QVector3D] = None, click2: Optional[QVector3D] = None
) -> Tuple[bool, str]:
    """Fillet corner with circular tangent arc of specified radius."""
    ok, msg, geo = compute_fillet_geometry(edge1, edge2, radius, click1, click2)
    if not ok:
        return False, msg

    V = geo["V"]
    pA_far = geo["pA_far"]
    pB_far = geo["pB_far"]
    T1 = geo["T1"]
    T2 = geo["T2"]
    arc_points = geo.get("arc_points", [])
    is_sharp = geo.get("is_sharp", False)

    update_mesh_corner(
        mesh, edge1, edge2, V, T1, T2, pA_far, pB_far, arc_points, is_sharp=is_sharp
    )

    if is_sharp:
        return True, tr("msg_extended_sharp")
    return True, tr("msg_fillet_created", r=radius, segs=len(arc_points) - 1)


def op_chamfer(
    mesh, edge1: Any, edge2: Any, dist1: float, dist2: float,
    click1: Optional[QVector3D] = None, click2: Optional[QVector3D] = None
) -> Tuple[bool, str]:
    """Chamfer corner with straight bevel segment."""
    ok, msg, geo = compute_chamfer_geometry(edge1, edge2, dist1, dist2, click1, click2)
    if not ok:
        return False, msg

    V = geo["V"]
    pA_far = geo["pA_far"]
    pB_far = geo["pB_far"]
    T1 = geo["T1"]
    T2 = geo["T2"]

    update_mesh_corner(
        mesh, edge1, edge2, V, T1, T2, pA_far, pB_far, arc_points=[], is_sharp=False
    )

    return True, tr("msg_chamfer_created", d1=dist1, d2=dist2)


# =============================================================================
# 5. TRANSACTION WRAPPER
# =============================================================================

def execute_transaction(viewport, mutate_func, success_msg: str = "") -> None:
    """Execute mutation safely inside IngeTrazo's undo system."""
    try:
        from core.history import SnapshotImport
        viewport.history.execute(SnapshotImport(mutate_func))
        viewport.notify_scene_changed()
        viewport.update()
        if success_msg:
            viewport.flash_status(success_msg, 4000)
    except Exception as exc:
        viewport.flash_status(f"Error: {exc}", 5000)


# =============================================================================
# 6. INTERACTIVE TOOLS (TRIM, FILLET, CHAMFER)
# =============================================================================

class CADTrimTool(Tool):
    """Interactive tool for Quick Trim and Boundary Trim."""
    uses_snap = True
    box_select = False

    def __init__(self, mode: str = "quick"):
        super().__init__()
        self.mode = mode
        self.name = "CAD Trim"
        self.cutter_edge = None
        self.hover_edge = None
        self.hover_pos = None
        self.trim_span: Optional[Tuple[QVector3D, QVector3D]] = None

    def on_activate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = self
        if viewport.active_tool is not self:
            viewport.set_active_tool(self)
            return

        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass

        if self.mode == "boundary":
            viewport.flash_status(tr("trim_start_boundary"), 6000)
        else:
            viewport.flash_status(tr("trim_start_quick"), 6000)
        viewport.update()

    def on_deactivate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = None
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.set_hover(None)
        viewport.update()

    def on_cancel(self, viewport) -> None:
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.flash_status(tr("trim_cancelled"), 2000)
        viewport.set_active_tool(None)
        viewport.update()

    def on_key(self, viewport, key: int, modifiers: Any) -> bool:
        if key == Qt.Key_Escape:
            self.on_cancel(viewport)
            return True
        return False

    def reset(self) -> None:
        self.cutter_edge = None
        self.hover_edge = None
        self.hover_pos = None
        self.trim_span = None

    def rubber_band_lines(self) -> List[Tuple[QVector3D, QVector3D]]:
        return []

    def on_hover(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        self.hover_edge = edge
        self.hover_pos = to_v3d(ctx.world)
        self.trim_span = None

        if edge is not None and self.mode == "quick":
            # Real-time preview of the span to be deleted!
            intersections = find_all_intersections_on_edge(vp.scene.mesh, edge, _SETTINGS["trim_tolerance"])
            s_pt, e_pt, _, _ = find_trim_span(edge, intersections, self.hover_pos)
            self.trim_span = (s_pt, e_pt)

        vp.set_hover(edge)
        vp.update()

    def on_click(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        if edge is None:
            return

        click_world = to_v3d(ctx.world)

        if self.mode == "boundary":
            if self.cutter_edge is None:
                # 1. Select Cutter
                self.cutter_edge = edge
                try:
                    vp.scene.clear_selection()
                    vp.scene.select([edge], mode="replace")
                except Exception:
                    pass
                vp.flash_status(tr("trim_cutter_selected"), 6000)
                vp.update()
            else:
                # 2. Trim Target against Cutter
                if edge == self.cutter_edge:
                    return

                res = {}
                def mutate(sc):
                    ok, msg = op_boundary_trim(sc.mesh, self.cutter_edge, edge, click_world)
                    res["msg"] = msg

                execute_transaction(vp, mutate)
                vp.flash_status(tr("status_next_line", msg=res.get("msg", tr("msg_trimmed"))), 5000)
                vp.update()

        else:
            # Quick Trim
            res = {}
            def mutate(sc):
                ok, msg = op_quick_trim(sc.mesh, edge, click_world)
                res["msg"] = msg

            execute_transaction(vp, mutate)
            self.trim_span = None
            vp.flash_status(tr("status_next_segment", msg=res.get("msg", tr("msg_trimmed"))), 5000)
            vp.update()


class CADFilletTool(Tool):
    """Interactive Fillet tool with dynamic VCB radius entry."""
    uses_snap = True
    box_select = False
    vcb_label = tr("vcb_radius")

    def __init__(self):
        super().__init__()
        self.name = "CAD Fillet"
        self.radius = _SETTINGS.get("fillet_radius", 0.50)
        self.edge1 = None
        self.click1 = None
        self.hover_edge = None
        self.hover_pos = None
        self.preview_arc: List[Tuple[QVector3D, QVector3D]] = []
        self.preview_trim: List[Tuple[QVector3D, QVector3D]] = []

    def on_activate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = self
        if viewport.active_tool is not self:
            viewport.set_active_tool(self)
            return

        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass

        r_str = tr("radius_value", v=self.radius) if self.radius > 0 else tr("radius_sharp")
        viewport.flash_status(tr("fillet_start", r=r_str), 6000)
        viewport.update()

    def on_deactivate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = None
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.set_hover(None)
        viewport.update()

    def on_cancel(self, viewport) -> None:
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.flash_status(tr("fillet_cancelled"), 2000)
        viewport.set_active_tool(None)
        viewport.update()

    def on_key(self, viewport, key: int, modifiers: Any) -> bool:
        if key == Qt.Key_Escape:
            self.on_cancel(viewport)
            return True
        return False

    def on_value(self, viewport, value: float) -> bool:
        """Called when user types a radius into IngeTrazo's VCB box and presses Enter."""
        if value < 0:
            viewport.flash_status(tr("radius_negative"), 3000)
            return False
        self.radius = value
        _SETTINGS["fillet_radius"] = value
        r_str = tr("radius_value", v=value) if value > 0 else tr("radius_sharp")
        viewport.flash_status(tr("radius_updated", r=r_str), 4000)
        self._calculate_preview()
        viewport.update()
        return True

    def reset(self) -> None:
        self.edge1 = None
        self.click1 = None
        self.hover_edge = None
        self.hover_pos = None
        self.preview_arc = []
        self.preview_trim = []

    def rubber_band_lines(self) -> List[Tuple[QVector3D, QVector3D]]:
        return self.preview_arc

    def on_hover(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        self.hover_edge = edge
        self.hover_pos = to_v3d(ctx.world)
        vp.set_hover(edge)

        self._calculate_preview()
        vp.update()

    def on_click(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        if edge is None:
            return

        click_world = to_v3d(ctx.world)

        if self.edge1 is None:
            # Pick Line 1
            self.edge1 = edge
            self.click1 = click_world
            try:
                vp.scene.clear_selection()
                vp.scene.select([edge], mode="replace")
            except Exception:
                pass
            vp.flash_status(tr("fillet_line1_selected", r=self.radius), 6000)
            vp.update()
        else:
            # Pick Line 2 -> Execute Fillet!
            if edge == self.edge1:
                return

            edge2 = edge
            click2 = click_world
            res = {}

            def mutate(sc):
                segs = _SETTINGS.get("fillet_segments", 16)
                ok, msg = op_fillet(sc.mesh, self.edge1, edge2, self.radius, segs, self.click1, click2)
                res["msg"] = msg

            execute_transaction(vp, mutate)

            try:
                vp.scene.clear_selection()
            except Exception:
                pass

            self.reset()
            vp.flash_status(tr("status_next_line1", msg=res.get("msg", tr("msg_completed"))), 5000)
            vp.update()

    def _calculate_preview(self) -> None:
        self.preview_arc = []
        self.preview_trim = []
        if self.edge1 is None or self.hover_edge is None or self.hover_edge == self.edge1:
            return

        ok, _, geo = compute_fillet_geometry(
            self.edge1, self.hover_edge, self.radius, self.click1, self.hover_pos
        )
        if not ok:
            return

        arc_pts = geo.get("arc_points", [])
        if arc_pts:
            for k in range(len(arc_pts) - 1):
                self.preview_arc.append((arc_pts[k], arc_pts[k + 1]))

        # Trimmed corner legs preview (highlighted in red)
        V = geo.get("V")
        T1 = geo.get("T1")
        T2 = geo.get("T2")
        if V and T1 and T2:
            self.preview_trim = [(V, T1), (V, T2)]


class CADChamferTool(Tool):
    """Interactive Chamfer tool with dynamic VCB distance entry."""
    uses_snap = True
    box_select = False
    vcb_label = tr("vcb_distance")

    def __init__(self):
        super().__init__()
        self.name = "CAD Chamfer"
        self.dist1 = _SETTINGS.get("chamfer_dist1", 0.30)
        self.dist2 = _SETTINGS.get("chamfer_dist2", 0.30)
        self.edge1 = None
        self.click1 = None
        self.hover_edge = None
        self.hover_pos = None
        self.preview_line: List[Tuple[QVector3D, QVector3D]] = []

    def on_activate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = self
        if viewport.active_tool is not self:
            viewport.set_active_tool(self)
            return

        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass

        viewport.flash_status(tr("chamfer_start", d=self.dist1), 6000)
        viewport.update()

    def on_deactivate(self, viewport) -> None:
        global _ACTIVE_TOOL
        _ACTIVE_TOOL = None
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.set_hover(None)
        viewport.update()

    def on_cancel(self, viewport) -> None:
        self.reset()
        try:
            viewport.scene.clear_selection()
        except Exception:
            pass
        viewport.flash_status(tr("chamfer_cancelled"), 2000)
        viewport.set_active_tool(None)
        viewport.update()

    def on_key(self, viewport, key: int, modifiers: Any) -> bool:
        if key == Qt.Key_Escape:
            self.on_cancel(viewport)
            return True
        return False

    def on_value(self, viewport, value: float) -> bool:
        if value <= 0:
            viewport.flash_status(tr("distance_positive"), 3000)
            return False
        self.dist1 = value
        self.dist2 = value
        _SETTINGS["chamfer_dist1"] = value
        _SETTINGS["chamfer_dist2"] = value
        viewport.flash_status(tr("distance_updated", d=value), 4000)
        self._calculate_preview()
        viewport.update()
        return True

    def reset(self) -> None:
        self.edge1 = None
        self.click1 = None
        self.hover_edge = None
        self.hover_pos = None
        self.preview_line = []

    def rubber_band_lines(self) -> List[Tuple[QVector3D, QVector3D]]:
        return self.preview_line

    def on_hover(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        self.hover_edge = edge
        self.hover_pos = to_v3d(ctx.world)
        vp.set_hover(edge)

        self._calculate_preview()
        vp.update()

    def on_click(self, ctx) -> None:
        vp = ctx.viewport
        edge = pick_edge_at(vp, ctx.screen.x(), ctx.screen.y())
        if edge is None:
            return

        click_world = to_v3d(ctx.world)

        if self.edge1 is None:
            self.edge1 = edge
            self.click1 = click_world
            try:
                vp.scene.clear_selection()
                vp.scene.select([edge], mode="replace")
            except Exception:
                pass
            vp.flash_status(tr("chamfer_line1_selected", d=self.dist1), 6000)
            vp.update()
        else:
            if edge == self.edge1:
                return

            edge2 = edge
            click2 = click_world
            res = {}

            def mutate(sc):
                ok, msg = op_chamfer(sc.mesh, self.edge1, edge2, self.dist1, self.dist2, self.click1, click2)
                res["msg"] = msg

            execute_transaction(vp, mutate)

            try:
                vp.scene.clear_selection()
            except Exception:
                pass

            self.reset()
            vp.flash_status(tr("status_next_line1", msg=res.get("msg", tr("msg_completed"))), 5000)
            vp.update()

    def _calculate_preview(self) -> None:
        self.preview_line = []
        if self.edge1 is None or self.hover_edge is None or self.hover_edge == self.edge1:
            return

        ok, _, geo = compute_chamfer_geometry(
            self.edge1, self.hover_edge, self.dist1, self.dist2, self.click1, self.hover_pos
        )
        if ok and geo.get("T1") and geo.get("T2"):
            self.preview_line = [(geo["T1"], geo["T2"])]


# =============================================================================
# 7. VIEWPORT 2D OVERLAY (RED HOVER SPAN & PREVIEWS)
# =============================================================================

def draw_trim_fillet_overlay(viewport, painter: QPainter) -> None:
    """Draw high-visibility custom overlay points and preview lines in the viewport."""
    tool = _ACTIVE_TOOL
    if tool is None or getattr(viewport, "active_tool", None) is not tool:
        return

    def project_pt(vec: QVector3D) -> Optional[QPointF]:
        try:
            xs, ys, front = viewport.world_to_pixels([[vec.x(), vec.y(), vec.z()]])
            if front[0]:
                return QPointF(float(xs[0]), float(ys[0]))
        except Exception:
            pass
        try:
            return viewport._world_to_pixel(vec)
        except Exception:
            return None

    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)

    # 1. Quick Trim Hover Span (Bright Glowing Red)
    if isinstance(tool, CADTrimTool) and tool.trim_span is not None:
        s_3d, e_3d = tool.trim_span
        s_screen = project_pt(s_3d)
        e_screen = project_pt(e_3d)
        if s_screen is not None and e_screen is not None:
            # Thick red line showing exactly what will be erased!
            pen_red = QPen(QColor(255, 40, 40, 230), 4.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_red)
            painter.drawLine(s_screen, e_screen)

            # Draw 'X' deletion markers at ends
            painter.setPen(QPen(QColor(255, 40, 40), 2.5))
            for pt in (s_screen, e_screen):
                painter.drawLine(pt.x() - 4, pt.y() - 4, pt.x() + 4, pt.y() + 4)
                painter.drawLine(pt.x() - 4, pt.y() + 4, pt.x() + 4, pt.y() - 4)

    # 2. Fillet Corner Arc & Trimmed Legs Preview
    if isinstance(tool, CADFilletTool):
        # Draw Fillet Arc (Bright Orange/Cyan)
        for s_3d, e_3d in tool.preview_arc:
            s_s = project_pt(s_3d)
            e_s = project_pt(e_3d)
            if s_s and e_s:
                painter.setPen(QPen(QColor(0, 200, 255), 2.5, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(s_s, e_s)

        # Draw Corner Legs to be Trimmed (Dashed Light Red)
        for s_3d, e_3d in tool.preview_trim:
            s_s = project_pt(s_3d)
            e_s = project_pt(e_3d)
            if s_s and e_s:
                painter.setPen(QPen(QColor(255, 80, 80, 180), 2.0, Qt.DashLine))
                painter.drawLine(s_s, e_s)

    # 3. Chamfer Bevel Preview
    if isinstance(tool, CADChamferTool):
        for s_3d, e_3d in tool.preview_line:
            s_s = project_pt(s_3d)
            e_s = project_pt(e_3d)
            if s_s and e_s:
                painter.setPen(QPen(QColor(0, 200, 255), 2.5, Qt.DashLine, Qt.RoundCap))
                painter.drawLine(s_s, e_s)

    painter.restore()


# =============================================================================
# 8. SETTINGS DIALOG
# =============================================================================

class TrimFilletSettingsDialog(QDialog):
    """Configuration dialog for CAD Trim & Fillet parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_title"))
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Fillet Group
        grp_fillet = QGroupBox(tr("dlg_fillet_group"), self)
        f_layout = QVBoxLayout(grp_fillet)

        row_r = QHBoxLayout()
        row_r.addWidget(QLabel(tr("dlg_default_radius")))
        self.spin_radius = QDoubleSpinBox()
        self.spin_radius.setRange(0.0, 1000.0)
        self.spin_radius.setSingleStep(0.1)
        self.spin_radius.setDecimals(3)
        self.spin_radius.setValue(_SETTINGS["fillet_radius"])
        row_r.addWidget(self.spin_radius)
        f_layout.addLayout(row_r)

        row_s = QHBoxLayout()
        row_s.addWidget(QLabel(tr("dlg_arc_segments")))
        self.spin_segs = QSpinBox()
        self.spin_segs.setRange(4, 64)
        self.spin_segs.setSingleStep(2)
        self.spin_segs.setValue(_SETTINGS["fillet_segments"])
        row_s.addWidget(self.spin_segs)
        f_layout.addLayout(row_s)

        layout.addWidget(grp_fillet)

        # Chamfer Group
        grp_chamfer = QGroupBox(tr("dlg_chamfer_group"), self)
        c_layout = QVBoxLayout(grp_chamfer)

        row_c1 = QHBoxLayout()
        row_c1.addWidget(QLabel(tr("dlg_distance1")))
        self.spin_c1 = QDoubleSpinBox()
        self.spin_c1.setRange(0.001, 1000.0)
        self.spin_c1.setSingleStep(0.05)
        self.spin_c1.setDecimals(3)
        self.spin_c1.setValue(_SETTINGS["chamfer_dist1"])
        row_c1.addWidget(self.spin_c1)
        c_layout.addLayout(row_c1)

        row_c2 = QHBoxLayout()
        row_c2.addWidget(QLabel(tr("dlg_distance2")))
        self.spin_c2 = QDoubleSpinBox()
        self.spin_c2.setRange(0.001, 1000.0)
        self.spin_c2.setSingleStep(0.05)
        self.spin_c2.setDecimals(3)
        self.spin_c2.setValue(_SETTINGS["chamfer_dist2"])
        row_c2.addWidget(self.spin_c2)
        c_layout.addLayout(row_c2)

        layout.addWidget(grp_chamfer)

        # Language Group
        grp_lang = QGroupBox(tr("dlg_language_group"), self)
        l_layout = QVBoxLayout(grp_lang)

        row_l = QHBoxLayout()
        row_l.addWidget(QLabel(tr("dlg_language_label")))
        self.combo_lang = QComboBox()
        self.combo_lang.addItem(tr("dlg_lang_auto"), "auto")
        self.combo_lang.addItem("English", "en")
        self.combo_lang.addItem("Español", "es")
        idx = self.combo_lang.findData(_SETTINGS.get("language", "auto"))
        self.combo_lang.setCurrentIndex(idx if idx >= 0 else 0)
        row_l.addWidget(self.combo_lang)
        l_layout.addLayout(row_l)

        lang_note = QLabel(tr("dlg_language_note"))
        lang_note.setWordWrap(True)
        l_layout.addWidget(lang_note)

        layout.addWidget(grp_lang)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton(tr("dlg_save"), self)
        btn_ok.clicked.connect(self._save_and_close)
        btn_cancel = QPushButton(tr("dlg_cancel"), self)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _save_and_close(self):
        _SETTINGS["fillet_radius"] = self.spin_radius.value()
        _SETTINGS["fillet_segments"] = self.spin_segs.value()
        _SETTINGS["chamfer_dist1"] = self.spin_c1.value()
        _SETTINGS["chamfer_dist2"] = self.spin_c2.value()
        save_language_preference(self.combo_lang.currentData())
        self.accept()


# =============================================================================
# 9. HIGH-DPI VECTOR ICON GENERATOR (DARK & LIGHT THEME ADAPTIVE)
# =============================================================================

def draw_trim_fillet_icon(icon_type: str) -> QIcon:
    """Render crisp, antialiased, theme-aware vector icons dynamically."""
    pm = QPixmap(48, 48)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)

    app = QApplication.instance()
    is_dark = True
    if app is not None:
        window_text = app.palette().windowText().color()
        is_dark = window_text.lightness() > 128

    blue_color = QColor(0, 160, 255) if is_dark else QColor(0, 120, 215)
    orange_color = QColor(255, 140, 0)
    red_color = QColor(240, 50, 50)

    pen_main = QPen(blue_color, 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    pen_cut = QPen(red_color, 2.5, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)

    if icon_type == "trim_quick":
        # Two crossing lines with one segment cut/dashed in red with scissors marker
        p.setPen(pen_main)
        p.drawLine(10, 38, 24, 24)
        p.drawLine(24, 24, 38, 10)  # cutter line
        p.drawLine(10, 10, 24, 24)  # kept line

        p.setPen(pen_cut)
        p.drawLine(24, 24, 38, 38)  # trimmed line in red

        # Small scissors/cut indicator
        p.setPen(Qt.NoPen)
        p.setBrush(red_color)
        p.drawEllipse(34, 34, 6, 6)

    elif icon_type == "trim_boundary":
        # Vertical boundary cutter line + horizontal trimmed lines
        p.setPen(QPen(orange_color, 3.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(24, 6, 24, 42)  # boundary cutter

        p.setPen(pen_main)
        p.drawLine(8, 24, 24, 24)  # kept line

        p.setPen(pen_cut)
        p.drawLine(24, 24, 40, 24)  # trimmed line

        p.setPen(Qt.NoPen)
        p.setBrush(red_color)
        p.drawEllipse(22, 22, 5, 5)

    elif icon_type == "fillet":
        # Corner with smooth tangent arc
        p.setPen(pen_main)
        p.drawLine(8, 40, 8, 22)
        p.drawLine(26, 40, 42, 40)

        # Smooth arc rounding the corner
        p.setPen(QPen(orange_color, 3.5, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(8, 22, 36, 36, 90 * 16, 90 * 16)

        # Dashed original sharp corner
        p.setPen(QPen(QColor(150, 150, 150), 1.5, Qt.DashLine))
        p.drawLine(8, 22, 8, 40)
        p.drawLine(8, 40, 26, 40)

    elif icon_type == "chamfer":
        # Corner with straight beveled chamfer segment
        p.setPen(pen_main)
        p.drawLine(8, 40, 8, 22)
        p.drawLine(26, 40, 42, 40)

        # Straight bevel line
        p.setPen(QPen(orange_color, 3.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(8, 22, 26, 40)

        # Dashed sharp corner
        p.setPen(QPen(QColor(150, 150, 150), 1.5, Qt.DashLine))
        p.drawLine(8, 22, 8, 40)
        p.drawLine(8, 40, 26, 40)

    elif icon_type == "settings":
        # Clean gear icon
        p.setPen(pen_main)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(16, 16, 16, 16)
        p.setPen(QPen(blue_color, 2.5))
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1 = 24 + 10 * math.cos(rad)
            y1 = 24 + 10 * math.sin(rad)
            x2 = 24 + 14 * math.cos(rad)
            y2 = 24 + 14 * math.sin(rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    p.end()
    return QIcon(pm)


# =============================================================================
# 10. TOOL ACTIVATION & DISPATCHER
# =============================================================================

def activate_trim_tool(app, mode: str = "quick") -> None:
    """Activate CAD Trim tool in the viewport."""
    vp = app.viewport
    tool = CADTrimTool(mode)
    vp.set_active_tool(tool)
    label_key = "tool_label_trim_quick" if mode == "quick" else "tool_label_trim_boundary"
    _sync_toolbar_selection(app, tr(label_key))


def activate_fillet_tool(app) -> None:
    """Activate CAD Fillet tool in the viewport."""
    vp = app.viewport
    tool = CADFilletTool()
    vp.set_active_tool(tool)
    _sync_toolbar_selection(app, tr("tool_label_fillet"))


def activate_chamfer_tool(app) -> None:
    """Activate CAD Chamfer tool in the viewport."""
    vp = app.viewport
    tool = CADChamferTool()
    vp.set_active_tool(tool)
    _sync_toolbar_selection(app, tr("tool_label_chamfer"))


def open_settings_dialog(app) -> None:
    """Open Settings dialog."""
    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    dlg = TrimFilletSettingsDialog(win)
    if dlg.exec():
        app.viewport.flash_status(tr("settings_updated"), 3000)


def _sync_toolbar_selection(app, label_name: str) -> None:
    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    if win is not None:
        for action in getattr(win, "_tool_actions", {}).values():
            action.setChecked(False)
        label = getattr(win, "_tool_label", None)
        if label is not None:
            label.setText(tr("tool_label_prefix", name=label_name))
    app.viewport.setFocus()


# =============================================================================
# 11. TOOLBAR & EXTENSION ENTRY POINT (SETUP)
# =============================================================================

def build_toolbar(app, win, actions_spec):
    """Build floating/dockable top toolbar for CAD Trim & Fillet."""
    toolbar_name = f"toolbar_{KEY}"
    tb = win.findChild(QToolBar, toolbar_name)
    if tb is None:
        tb = QToolBar("CAD Trim & Fillet", win)
        tb.setObjectName(toolbar_name)
        tb.setMovable(True)
        tb.setFloatable(True)
        tb.setIconSize(QSize(24, 24))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        win.addToolBar(Qt.TopToolBarArea, tb)

    for icon_key, title, tooltip, callback in actions_spec:
        action = QAction(draw_trim_fillet_icon(icon_key), title, tb)
        action.setToolTip(f"<b>{title}</b><br>{tooltip}{_credits_html()}")
        action.setStatusTip(f"{title} — {tooltip}")
        action.triggered.connect(lambda _checked=False, fn=callback: fn())
        tb.addAction(action)

    return tb


def setup(app) -> None:
    """Official IngeTrazo extension entry point."""
    global _GLOBAL_APP
    _GLOBAL_APP = app

    actions_spec = [
        (
            "trim_quick",
            tr("act_quick_title"),
            tr("act_quick_tip"),
            lambda: activate_trim_tool(app, "quick"),
        ),
        (
            "trim_boundary",
            tr("act_boundary_title"),
            tr("act_boundary_tip"),
            lambda: activate_trim_tool(app, "boundary"),
        ),
        (
            "fillet",
            tr("act_fillet_title"),
            tr("act_fillet_tip"),
            lambda: activate_fillet_tool(app),
        ),
        (
            "chamfer",
            tr("act_chamfer_title"),
            tr("act_chamfer_tip"),
            lambda: activate_chamfer_tool(app),
        ),
        (
            "settings",
            tr("act_settings_title"),
            tr("act_settings_tip"),
            lambda: open_settings_dialog(app),
        ),
    ]

    # 1. Extensions Menu Registration
    sub_menu = app.add_menu("CAD Trim & Fillet")
    if sub_menu is not None:
        for icon_key, title, tooltip, callback in actions_spec:
            act = sub_menu.addAction(draw_trim_fillet_icon(icon_key), title)
            act.setToolTip(tooltip)
            act.setStatusTip(f"{title}: {tooltip}")
            act.triggered.connect(lambda _c=False, fn=callback: fn())

        sub_menu.addSeparator()
        info_act = sub_menu.addAction(tr("author_line", a=AUTHOR))
        info_act.setEnabled(False)
        if current_language() == "es":
            translator_act = sub_menu.addAction(tr("translator_line", t=TRANSLATOR))
            translator_act.setEnabled(False)
    else:
        for icon_key, title, tooltip, callback in actions_spec:
            app.add_menu_action(f"CAD Trim & Fillet: {title}", callback, tip=tooltip)

    # 2. Viewport Right-Click Context Menu Hook
    def context_menu_hook(menu: QMenu, selection) -> None:
        menu.addSeparator()
        title_act = menu.addAction(f"— CAD Trim & Fillet ({AUTHOR}) —")
        title_act.setEnabled(False)

        act_qt = menu.addAction(draw_trim_fillet_icon("trim_quick"), tr("act_quick_title"))
        act_qt.triggered.connect(lambda _c=False: QTimer.singleShot(0, lambda: activate_trim_tool(app, "quick")))

        act_f = menu.addAction(draw_trim_fillet_icon("fillet"), tr("act_fillet_title") + "...")
        act_f.triggered.connect(lambda _c=False: QTimer.singleShot(0, lambda: activate_fillet_tool(app)))

        act_ch = menu.addAction(draw_trim_fillet_icon("chamfer"), tr("act_chamfer_title") + "...")
        act_ch.triggered.connect(lambda _c=False: QTimer.singleShot(0, lambda: activate_chamfer_tool(app)))

    app.add_context_menu(context_menu_hook)

    # 3. Viewport 2D Overlay Drawing Hook (Hover red spans & Fillet arc preview)
    app.add_overlay(draw_trim_fillet_overlay)

    # 4. Top Toolbar Creation
    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    if win is not None:
        build_toolbar(app, win, actions_spec)
     
