from XRPLib.defaults import *
from XRPLib.board import Board
from XRPLib.rangefinder import Rangefinder
from XRPLib.differential_drive import DifferentialDrive
from time import sleep
import sys
import qwiic_twist

# Initialize XRPLib components
print("Initializing XRP components.")
rangefinder = Rangefinder.get_default_rangefinder()  # Default rangefinder instance
drivetrain = DifferentialDrive.get_default_differential_drive()  # Differential drive instance
board = Board.get_default_board()  # Board for button and LED control
data_delay = 100

# Initialize Qwiic Twist
print("\nInitializing Qwiic\n")
myTwist = qwiic_twist.QwiicTwist()

if not myTwist.connected:
    print("The Qwiic twist device isn't connected to the system. Please check your connection", file=sys.stderr)
else:
    print("Qwiic Twist is connected.")
    
# Reset twist function
def reset_twist(myTwist):
    myTwist.begin()
    myTwist.set_color(0, 0, 0)
    myTwist.set_connect_red(0)
    myTwist.set_connect_blue(0)
    myTwist.set_connect_green(0)
    #LED Vals set to 0, twist relations set to none	

#seting the inital color to blue and if twisted it cycles to purple
def state_relation(myTwist):
    myTwist.set_color(0, 0, 255)
    myTwist.set_connect_red(255)
    
def exit_relation(myTwist):
    myTwist.set_color(255,255,255)
    myTwist.set_connect_green(-255)
    # shift between purple and white

#starts at green and can slowly transition to yellow to red.
def hl_relation(myTwist):
    myTwist.set_color(0, 255, 0)
    myTwist.set_connect_red(255)
    myTwist.set_connect_green(-255)

#selects between states (blue and purple)
def check_state(myTwist):
    i = 0
    if ((myTwist.get_red() == 0) and (myTwist.is_pressed())):
        i = 1
    if ((myTwist.get_red() > 0) and (myTwist.is_pressed())):
        i = 2
    if ((myTwist.get_green() > 0) and (myTwist.is_pressed())):
        i = 3
    return i

# Function for data collection
def collect_data(high_list, low_list):

    print('Collect Data')
    reset_twist(myTwist)

    hl_relation(myTwist)
    sleep(0.5)
    print("- set height (green = high, red = low), click to take data\n")

    while True:
        if myTwist.is_pressed():
            if myTwist.get_green() > 0:
                height = "high"
                distance = rangefinder.distance()
                high_list.append(distance)
            elif myTwist.get_red() > 0:
                height = "low"
                distance = rangefinder.distance()
                low_list.append(distance)

            print(f'New Data - height: {height}, distance: {distance}')

            # Wait to prevent double readings
            sleep(0.75)
            reset_twist(myTwist)
            print('** Ready for next data collection **')
            break

# determine if data point is closer to high or low data
def nearestNeighbor(high_list, low_list):
    print('Click the twist to check the height of an object')

    if myTwist.is_pressed():   # when pressed check distance
        current_distance = rangefinder.distance()
        print("current distance is", current_distance)

        closest_high = high_list[0]
        for i in high_list:
            if abs(i - current_distance) < abs(closest_high - current_distance):
                closest_high = i
                print('closest_high', closest_high)
                
        closest_low = low_list[0]
        for i in low_list:
            if abs(i - current_distance) < abs(closest_low - current_distance):
                closest_low = i
                print('closest low', closest_low)

        if abs(closest_high - current_distance) < abs(closest_low - current_distance):
            print("High furniture")

            myTwist.set_color(0, 255, 0)
            sleep(3)
        else:
             print("Low furniture")
             myTwist.set_color(255, 0, 0)
             sleep(3)

        sleep(0.1)

# Main task function
def main():
    high_list = []
    low_list = []

    reset_twist(myTwist)
    myTwist.set_color(0, 0, 255)

    print('Nearest Neighbor Application:')
    print('- click on the blue button to collect a data point')
    
    while True:
        print("Click blue to continue adding data or click purple to start testing your nearest neighbor.")
        while len(high_list) < 2 or len(low_list) < 2:
            if check_state(myTwist) == 1:
                collect_data(high_list, low_list)
                if len(high_list) >= 2 and len(low_list) >= 2:
                    state_relation(myTwist)
                else:
                    myTwist.set_color(0, 0, 255)
 
        print("Click purple to continue testing or click white to exit program.")             
        while len(high_list) >= 2 and len(low_list) >= 2:
            if check_state(myTwist) == 1:
                collect_data()
                reset_twist(myTwist)
                state_relation(myTwist)
            
            if check_state(myTwist) == 2:
                nearestNeighbor(high_list, low_list)
                reset_twist(myTwist)
                exit_relation(myTwist)
                #resetting all values for next use
            if check_state(myTwist) == 3:
                reset_twist(myTwist)
                myTwist.set_color(0, 0, 255)
                high_list = []
                low_list = []
                print('Data Reset')

        sleep(0.5)

# Run the Main Task
print("Starting main task.")
main()
