import cv2
import time
import numpy as np
import serial.tools.list_ports

# Store time to calc FPS
pTime = 0
cTime = 0

# Window capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not opened. Try indices 1, 2, or a different backend.")

win = "Detect Squares"
cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)  # create window first
width = 1280
height = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

# Arduino
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portsList = []

for port in ports:
    portsList.append(str(port))
    print(str(port))

com = input("Select Com Port: ")

for i in range(len(portsList)):
    portName = "COM" + str(com)
    if portsList[i].startswith(portName): # check if port exists in list
        usedPort = portName

serialInst.baudrate = 9600
serialInst.port = usedPort
serialInst.open()




x1 = 0
x2 = 0
y1 = 0
y2 = 0
currX = 0
currY = 0
rec = False
drawing = False

def drawRectangle(action, x, y, flags, *userdata):
    global x1, y1, x2, y2, currX, currY, rec, drawing
    if action == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        rec = False
        x1 = x
        y1 = y
        # setting current mouse position to prevent random rectangles when click
        currX = x
        currY = y
    elif action == cv2.EVENT_LBUTTONUP:
        rec = True
        drawing = False
        x2 = x
        y2 = y


    if action == cv2.EVENT_MOUSEMOVE and drawing:
        currX = x
        currY = y


cv2.setMouseCallback("Detect Squares", drawRectangle)

def grid(img, rows, columns, borderColour, borderSize):
    gridX = (x2 - x1) / rows
    gridY = (y2 - y1) / columns

    lowerBound = np.array([40, 100, 20])
    upperBound = np.array([100, 255, 255])

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) # Convert image from BGR to HSV
    mask = cv2.inRange(hsv, lowerBound, upperBound)

    array = np.zeros((rows, columns), dtype=bool)

    for i in range(rows):
        for j in range(columns):
            startX = x1 + i * gridX
            startY = y1 + j * gridY
            endX = startX + gridX
            endY = startY + gridY
            cv2.rectangle(img, (int(startX), int(startY)), (int(endX), int(endY)), borderColour, borderSize)
            cell_mask = mask[int(startY):int(endY), int(startX):int(endX)]

            contours, hierarchy = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            array[i][j] = 0
            if len(contours) != 0:
                for contour in contours:
                    if cv2.contourArea(contour) > (gridX*gridY) / 3: # check if colour is at least 33% of grid box size
                        array[i][j] = 1

    print(array)
    serialInst.write(array.astype(np.uint8).flatten().tobytes())


gridRows = int(input("Rows: "))
gridColumns = int(input("Columns: "))
while True:
    # Error check
    success, img = cap.read()
    if not success or img is None:
        continue

    # Draw rectangle
    if rec:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        grid(img, gridRows, gridColumns, (0, 255, 0), 2)

    if drawing:
        cv2.rectangle(img, (x1, y1), (currX, currY), (0, 255, 0), 2)


    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str("FPS: ") + str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 200, 50), 2)

    # Display Cam
    cv2.imshow(win, img)
    cv2.waitKey(1)