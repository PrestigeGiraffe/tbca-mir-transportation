import cv2
import time
import numpy as np
# import serial.tools.list_ports
from pycomm3 import LogixDriver

from enum import Enum, auto

drawMode = -1


class DrawModes(Enum):
    GRID = auto()
    SINGLE_RECT = auto()
    MULTI_RECT = auto()


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

# PLC
PLC_IP = '192.168.1.100/0'
plc = LogixDriver(PLC_IP)
plc.open()

# Arduino
# ports = serial.tools.list_ports.comports()
# serialInst = serial.Serial()
# portsList = []

# for port in ports:
#     portsList.append(str(port))
#     print(str(port))

# com = input("Select Com Port: ")

# for i in range(len(portsList)):
#     portName = "COM" + str(com)
#     if portsList[i].startswith(portName): # check if port exists in list
#         usedPort = portName

# serialInst.baudrate = 9600
# serialInst.port = usedPort
# serialInst.open()


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
    xmin = min(x1, x2)
    xmax = max(x1, x2)
    ymin = min(y1, y2)
    ymax = max(y1, y2)
    gridX = (xmax - xmin) / columns
    gridY = (ymax - ymin) / rows

    lowerBound = np.array([40, 50, 20])
    upperBound = np.array([80, 255, 255])

    # ALL COLOUR RANGES (TESTING)
    # lowerBound = np.array([0, 0, 0])
    # upperBound = np.array([255, 255, 255])

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  # Convert image from BGR to HSV
    mask = cv2.inRange(hsv, lowerBound, upperBound)

    # SHOW MASK FOR TESTING PURPOSES
    # cv2.imshow("Mask", mask)

    array = np.zeros((rows, columns), dtype=bool)

    for i in range(rows):
        for j in range(columns):
            startX = xmin + j * gridX
            startY = ymin + i * gridY
            endX = startX + gridX
            endY = startY + gridY
            cv2.rectangle(img, (int(startX), int(startY)), (int(endX), int(endY)), borderColour, borderSize)
            cell_mask = mask[int(startY):int(endY), int(startX):int(endX)]

            contours, hierarchy = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            array[i][j] = 0
            if len(contours) != 0:
                for contour in contours:
                    # if the ratio of target coloured pixels is greater than threshold
                    pixelRatio = np.count_nonzero(cell_mask) / cell_mask.size
                    detectionThreshold = 0.5
                    array[i][j] = pixelRatio > detectionThreshold

    print(array)
    # serialInst.write(array.astype(np.uint8).flatten().tobytes())
    # print(plc.get_plc_info())

    # WRITE ARRAY TO PLC
    flat = array.astype(np.int16).flatten().tolist()  # Flatten array and convert to DINT
    # data = [rows, columns] + flat
    startIndex = "30"
    result = plc.write(f'AMR_7.Register[{startIndex}]{{ {len(flat)} }}', flat)
    print("Write result:", result)

    plc.write("CV_Grid_Rows", rows)
    plc.write("CV_Grid_Columns", columns)


while True:
    # Error check
    success, img = cap.read()
    if not success or img is None:
        continue

    # Draw rectangle
    if rec:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if drawMode == DrawModes.GRID:
            grid(img, gridRows, gridColumns, (0, 255, 0), 2)

    if drawing:
        cv2.rectangle(img, (x1, y1), (currX, currY), (0, 255, 0), 2)

    # UI Text
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str("FPS: ") + str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 200, 50), 2)
    cv2.putText(img, str("EXIT (q)"), (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 255), 4)
    cv2.putText(img, str("GRID (g)"), (10, 650), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 255, 50), 4)
    cv2.putText(img, str("EXIT DRAWING (c)"), (10, 600), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 255, 50), 4)

    cv2.putText(img, str(f'MODE: {drawMode}'), (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 4)

    # User inputs
    key = cv2.waitKey(1) & 0xFF

    # CHANGE DRAW MODE
    if key == ord('c'):
        drawing = False
        rec = False

    if key == ord('g'):
        gridRows = int(input("Rows: "))
        gridColumns = int(input("Columns: "))
        drawMode = DrawModes.GRID
        drawing = False
        rec = False

    # --- EXIT ON 'q' ---
    if key == ord('q'):
        break

    # Display Cam
    cv2.imshow(win, img)

cv2.destroyAllWindows()