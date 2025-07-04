import cv2
import mediapipe as mp
import numpy as np
from math import sqrt, pi

mp_pose = mp.solutions.pose
LND = mp_pose.PoseLandmark


def extract_measurements_from_images(front_img_path: str,
                                     side_img_path : str,
                                     height_cm     : float) -> dict:
    """
    Returns shoulder width, torso height and body depth **already in cm**.
    The conversion factor (px → cm) is derived from the person's true
    height that the user's input.
    """
    kp_front = _get_landmarks(front_img_path)
    kp_side  = _get_landmarks(side_img_path)
    
    # Get image dimensions for better scaling
    img_front = cv2.imread(front_img_path)
    img_side = cv2.imread(side_img_path)
    h_front, w_front = img_front.shape[:2]
    h_side, w_side = img_side.shape[:2]

    return _calculate_measurements(kp_front, kp_side, height_cm, w_front, h_front, w_side, h_side)


def extract_measurements_from_images_with_bytes(front_bytes: bytes,
                                     side_bytes: bytes,
                                     height_cm: float) -> dict:
    kp_front = _get_landmarks_from_bytes(front_bytes)
    kp_side  = _get_landmarks_from_bytes(side_bytes)
    
    # Get image dimensions from bytes
    file_bytes_front = np.frombuffer(front_bytes, np.uint8)
    img_front = cv2.imdecode(file_bytes_front, cv2.IMREAD_COLOR)
    file_bytes_side = np.frombuffer(side_bytes, np.uint8)
    img_side = cv2.imdecode(file_bytes_side, cv2.IMREAD_COLOR)
    
    h_front, w_front = img_front.shape[:2]
    h_side, w_side = img_side.shape[:2]

    return _calculate_measurements(kp_front, kp_side, height_cm, w_front, h_front, w_side, h_side)


def _calculate_measurements(kp_front, kp_side, height_cm, w_front, h_front, w_side, h_side):
    """Enhanced measurement calculations with better accuracy and additional metrics."""
    
    # === Improved Height Reference ===
    # Use eye landmarks to better approximate head top, then to ankles for more accurate scaling
    eye_y = np.mean([
        kp_front[LND.LEFT_EYE].y,
        kp_front[LND.RIGHT_EYE].y
    ])
    # Approximate head top by moving upward from eye level
    head_top_y = eye_y - 0.08  # Reduced from 0.1 for better accuracy
    
    # Use ankles instead of heels for more consistent reference
    ankle_y = np.mean([
        kp_front[LND.LEFT_ANKLE].y,
        kp_front[LND.RIGHT_ANKLE].y
    ])
    
    px_height = (ankle_y - head_top_y) * h_front
    px_to_cm = height_cm / (px_height + 1e-6)  # Add small epsilon to prevent division by zero
    
    # === Enhanced Shoulder Width ===
    px_shoulder = _euclidean_distance(
        kp_front[LND.LEFT_SHOULDER], 
        kp_front[LND.RIGHT_SHOULDER], 
        w_front, h_front
    )
    shoulder_cm = px_shoulder * px_to_cm
    
    # === Improved Torso Height (using midpoints for better accuracy) ===
    mid_shoulder_y = (kp_front[LND.LEFT_SHOULDER].y + kp_front[LND.RIGHT_SHOULDER].y) / 2
    mid_hip_y = (kp_front[LND.LEFT_HIP].y + kp_front[LND.RIGHT_HIP].y) / 2
    px_torso = abs(mid_shoulder_y - mid_hip_y) * h_front
    torso_height_cm = px_torso * px_to_cm
    
    # === Enhanced Side Depth ===
    # Use the same scaling factor but with pixel-accurate distance
    px_depth = _euclidean_distance(
        kp_side[LND.LEFT_SHOULDER], 
        kp_side[LND.LEFT_HIP], 
        w_side, h_side
    )
    side_depth_cm = px_depth * px_to_cm
    
    # === Additional Measurements ===
    
    # Hip width
    px_hip_width = _euclidean_distance(
        kp_front[LND.LEFT_HIP], 
        kp_front[LND.RIGHT_HIP], 
        w_front, h_front
    )
    hip_width_cm = px_hip_width * px_to_cm
    
    # Arm length (shoulder to wrist)
    px_arm_length = _euclidean_distance(
        kp_front[LND.LEFT_SHOULDER], 
        kp_front[LND.LEFT_WRIST], 
        w_front, h_front
    )
    arm_length_cm = px_arm_length * px_to_cm
    
    # Leg length (hip to ankle)
    px_leg_length = _euclidean_distance(
        kp_front[LND.LEFT_HIP], 
        kp_front[LND.LEFT_ANKLE], 
        w_front, h_front
    )
    leg_length_cm = px_leg_length * px_to_cm
    
    # === ENHANCED WAIST CALCULATIONS (Improved from first code) ===
    
    # Method 1: Geometric estimation with improved ratios
    waist_width_cm = shoulder_cm * 0.7  # More accurate ratio from first code
    waist_depth_cm = side_depth_cm * 0.8  # Waist depth relative to torso depth
    
    # Elliptical circumference approximation (from first code)
    waist_circumference_geometric = pi * sqrt((waist_width_cm**2 + waist_depth_cm**2) / 2)
    
    # Method 2: Regression-based estimation (from first code)
    # This uses anthropometric relationships and requires weight input
    # For now, we'll estimate weight based on height and build
    estimated_weight = _estimate_weight_from_measurements(height_cm, shoulder_cm, side_depth_cm)
    waist_circumference_regression = (0.35 * shoulder_cm) + (0.25 * height_cm) + (0.4 * estimated_weight) - 20
    
    # Method 3: Improved simple estimation
    waist_circumference_simple = (waist_width_cm + waist_depth_cm) * pi / 2
    
    # Method 4: Average of methods for better accuracy
    waist_circumference_average = np.mean([
        waist_circumference_geometric,
        waist_circumference_regression,
        waist_circumference_simple
    ])
    
    # === Quality Checks and Bounds (with caps from first code) ===
    shoulder_cm = min(max(shoulder_cm, 25), 45)  # Cap at 45cm like first code
    torso_height_cm = min(max(torso_height_cm, 20), 60)  # Cap at 60cm like first code
    side_depth_cm = min(max(side_depth_cm, 15), 35)  # Cap at 35cm like first code
    
    # Cap waist measurements
    waist_circumference_geometric = min(waist_circumference_geometric, 130)  # Cap from first code
    waist_circumference_regression = min(waist_circumference_regression, 130)
    waist_circumference_average = min(waist_circumference_average, 130)
    
    # === Return Enhanced Results ===
    return {
        # Original measurements (maintained for compatibility)
        "height_cm"   : float(height_cm),
        "shoulder_cm" : float(shoulder_cm),
        "torso_height": float(torso_height_cm),
        "side_depth"  : float(waist_circumference_regression),
        
        # Additional measurements
        "hip_width_cm": float(hip_width_cm),
        "arm_length_cm": float(arm_length_cm),
        "leg_length_cm": float(leg_length_cm),
        "waist_width_cm": float(waist_width_cm),
        
        # Enhanced waist circumference calculations
        "waist_circumference_geometric": float(waist_circumference_geometric),
        "waist_circumference_regression": float(waist_circumference_regression),
        "waist_circumference_simple": float(waist_circumference_simple),
        "waist_circumference_average": float(waist_circumference_average),  # New: averaged result
        
        # Scaling information
        "px_to_cm_scale": float(px_to_cm),
        "measurement_quality": _assess_measurement_quality(kp_front, kp_side),
        "estimated_weight_kg": float(estimated_weight)  # New: for transparency
    }


def _estimate_weight_from_measurements(height_cm, shoulder_cm, depth_cm):
    """
    Estimate weight based on body measurements for regression calculation.
    This is a rough approximation based on typical body proportions.
    """
    # Simple estimation based on build indicators
    # BMI estimation: assume average BMI of 22-24 for normal build
    base_weight = (height_cm / 100) ** 2 * 23  # Base weight from height
    
    # Adjust based on shoulder width (indicator of frame size)
    frame_adjustment = (shoulder_cm - 38) * 1.5  # 38cm is average shoulder width
    
    # Adjust based on depth (indicator of body thickness)
    depth_adjustment = (depth_cm - 25) * 2  # 25cm is average depth
    
    estimated_weight = base_weight + frame_adjustment + depth_adjustment
    
    # Reasonable bounds for adult weight
    return max(45, min(estimated_weight, 120))  # Between 45-120 kg


def _get_landmarks(img_path: str):
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        raise FileNotFoundError(img_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Use higher model complexity for better accuracy
    with mp_pose.Pose(static_image_mode=True, model_complexity=2) as pose:
        res = pose.process(img_rgb)
        if not res.pose_landmarks:
            raise ValueError(f"No landmarks in {img_path}")
        return res.pose_landmarks.landmark


def _get_landmarks_from_bytes(image_bytes: bytes):
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Invalid image bytes")
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Use higher model complexity for better accuracy
    with mp_pose.Pose(static_image_mode=True, model_complexity=2) as pose:
        res = pose.process(img_rgb)
        if not res.pose_landmarks:
            raise ValueError("No landmarks detected in image")
        return res.pose_landmarks.landmark


def _dist(a, b):
    """Original distance function for normalized coordinates (kept for compatibility)."""
    return np.linalg.norm(
        np.array([a.x, a.y]) - np.array([b.x, b.y])
    )


def _euclidean_distance(p1, p2, w, h):
    """
    Enhanced distance calculation that accounts for actual pixel dimensions.
    More accurate than normalized coordinate distance.
    """
    return sqrt((p1.x - p2.x)**2 * w**2 + (p1.y - p2.y)**2 * h**2)


def _assess_measurement_quality(kp_front, kp_side):
    """
    Assess the quality of pose detection for measurement reliability.
    Returns a quality score and potential issues.
    """
    quality_issues = []
    
    # Check visibility of key landmarks
    key_landmarks_front = [LND.LEFT_SHOULDER, LND.RIGHT_SHOULDER, LND.LEFT_HIP, 
                          LND.RIGHT_HIP, LND.LEFT_ANKLE, LND.RIGHT_ANKLE]
    
    for landmark in key_landmarks_front:
        if kp_front[landmark].visibility < 0.5:
            quality_issues.append(f"Low visibility: {landmark.name}")
    
    # Check for reasonable body proportions
    shoulder_to_hip = _dist(kp_front[LND.LEFT_SHOULDER], kp_front[LND.LEFT_HIP])
    hip_to_ankle = _dist(kp_front[LND.LEFT_HIP], kp_front[LND.LEFT_ANKLE])
    
    # Legs should typically be longer than torso
    if hip_to_ankle < shoulder_to_hip * 0.8:
        quality_issues.append("Unusual body proportions detected")
    
    # Check symmetry
    left_shoulder_hip = _dist(kp_front[LND.LEFT_SHOULDER], kp_front[LND.LEFT_HIP])
    right_shoulder_hip = _dist(kp_front[LND.RIGHT_SHOULDER], kp_front[LND.RIGHT_HIP])
    
    if abs(left_shoulder_hip - right_shoulder_hip) > 0.1:
        quality_issues.append("Body asymmetry detected - pose may be angled")
    
    if not quality_issues:
        return {"score": "excellent", "issues": []}
    elif len(quality_issues) <= 2:
        return {"score": "good", "issues": quality_issues}
    else:
        return {"score": "poor", "issues": quality_issues}