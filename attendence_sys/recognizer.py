import face_recognition
import numpy as np
import cv2
import os
import time

def Recognizer(details):
    video = cv2.VideoCapture(0)
    known_face_encodings = []
    known_face_names = []
    recognized_names = []
    
    try:
        # Build image directory path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_dir = os.path.join(base_dir, 'static', 'images', 'Student_Images',
                               details['branch'], details['year'], details['section'])
        
        if not os.path.exists(image_dir):
            raise FileNotFoundError(f"Student images directory not found: {image_dir}")

        # Load known faces
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                if file.lower().endswith(('jpg', 'png', 'jpeg')):
                    path = os.path.join(root, file)
                    try:
                        image = face_recognition.load_image_file(path)
                        encodings = face_recognition.face_encodings(image)
                        if encodings:
                            label = os.path.splitext(file)[0]  # Use filename without extension as ID
                            known_face_names.append(label)
                            known_face_encodings.append(encodings[0])
                    except Exception as e:
                        print(f"Error processing {file}: {str(e)}")

        if not known_face_encodings:
            raise ValueError("No valid face encodings found in student images")

        # Recognition loop
        start_time = time.time()
        while True:
            ret, frame = video.read()
            if not ret:
                break

            # Process frame
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            current_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                name = "Unknown"
                
                if True in matches:
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        if name not in recognized_names:
                            recognized_names.append(name)
                current_names.append(name)

            # Display results
            for (top, right, bottom, left), name in zip(face_locations, current_names):
                top, right, bottom, left = [coord * 4 for coord in [top, right, bottom, left]]
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), 
                          cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

            cv2.imshow("Face Recognition - Press 'q' to finish", frame)
            
            # Exit conditions (q key or 30 seconds timeout)
            if cv2.waitKey(1) & 0xFF == ord('q') or time.time() - start_time > 30:
                break

    except Exception as e:
        print(f"Recognition error: {str(e)}")
    finally:
        video.release()
        cv2.destroyAllWindows()
        # Additional cleanup for any remaining windows
        for i in range(1, 5):
            cv2.waitKey(1)
    
    return recognized_names