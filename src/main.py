import cv2
from emotion_detection import EmotionDetector
from gaze_tracker import GazeTracker
from head_pose_tracker import HeadPoseTracker
from blink_tracker import BlinkTracker
from behavior_logic import BehaviorAnalysis
from logger import Logger

emotion_engine = EmotionDetector(r'F:\MAJU\6th Semester\AI\Project\Interview-Detection-System\models\interview_emotion_final_94.keras')
gaze_engine = GazeTracker()
head_engine = HeadPoseTracker()
blink_engine = BlinkTracker()
analyzer = BehaviorAnalysis()
logger = Logger()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    emotion, conf = emotion_engine.predict_emotion(frame)
    gaze = gaze_engine.get_gaze_ratio(frame)
    yaw, pitch, roll = head_engine.get_head_pose(frame)
    blink_rate = blink_engine.update_blink(frame)

    score = analyzer.evaluate(emotion, gaze, blink_rate, yaw)
    logger.log(emotion, gaze, score, blink_rate, yaw)

    cv2.putText(frame, f"Emotion: {emotion}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0),2)
    cv2.putText(frame, f"Gaze: {gaze}", (10,65), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,0),2)
    cv2.putText(frame, f"Score: {score}", (10,100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255),2)

    cv2.imshow("Interview AI", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()