from XRPLib.rangefinder import Rangefinder
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.board import Board
import time
import qwiic_twist

# Initialize XRPLib components
rangefinder = Rangefinder.get_default_rangefinder()  # Default rangefinder instance
drivetrain = DifferentialDrive.get_default_differential_drive()  # Differential drive instance
board = Board.get_default_board()  # Board for button and LED control


print("\nInitializing Qwiic\n")
myTwist = qwiic_twist.QwiicTwist()

if myTwist.connected == False:
    print("The Qwiic twist device isn't connected to the system. Please check your connection", \
	    file=sys.stderr)
	    
def reset_twist(myTwist):
    myTwist.begin()
    myTwist.set_color(0, 0, 0)
    myTwist.set_connect_red(0)
    myTwist.set_connect_blue(0)
    myTwist.set_connect_green(0)
    #LED Vals set to 0, twist relations set to none	

def state_relation(myTwist):
    myTwist.set_color(0, 0, 255)
    myTwist.set_connect_red(255)
    #seting the inital color to blue and if twisted it cycles to purple
    
def throttle_relation(myTwist):
    myTwist.set_color(0, 255, 0)
    myTwist.set_connect_red(10)
    myTwist.set_connect_green(-10)
    #starts at green and can slowly transition to yellow to red.
    
def exit_relation(myTwist):
    myTwist.set_color(255,255,255)
    myTwist.set_connect_green(-255)
    myTwist.set_connect_red(-255)

def check_state(myTwist):
    i = 0
    if ((myTwist.get_red() == 0) and (myTwist.is_pressed())):
        i = 1
    if ((myTwist.get_red() > 0) and (myTwist.is_pressed())):
        i = 2
    if ((myTwist.get_green() > 0) and (myTwist.is_pressed())):
        i = 3
    return i
    #selects between states (blue and purple)
    
# Calculate slope and intercept for linear regression
def calculate_linear_regression(x, y, n):
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum([xi * yi for xi, yi in zip(x, y)])
    sum_xx = sum([xi**2 for xi in x])
    
    m = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
    c = (sum_y - m * sum_x) / n
    
    return m, c

# Data Collection
def collect_data(distances, speeds, myTwist):
    # Confirm taking data
    print('Collect Data')
    
    reset_twist(myTwist)
    
    throttle_relation(myTwist)
    time.sleep(0.5)
    
    print("\n- set speed (green = full speed, red = stop)")
    print("- click to take distance and speed data\n")
    
    i = 0
    while (i == 0):
        if (myTwist.is_pressed()):
            speed = (myTwist.get_green()/2.5)
            print (speed)
            # Get Distance Measurement
            distance = rangefinder.distance()
            i = 1

    # Store Data
    distances.append(distance)
    speeds.append(speed)
    
    print('New Data:')
    print('- Distances:', distances)
    print('- Speeds:', speeds)

    # Wait to Prevent Double Readings
    time.sleep(0.75)
    print('** Ready for next datapoint')

# Controller
def proportional_control(distances, speeds):
    # Confirm running code
    if len(distances) < 2 or len(speeds) < 2:
        print('ERROR: need more data')
        return
    
    print('Calculating')
    time.sleep(0.75)

    # Calculate coefficients for line of best fit
    m, c = calculate_linear_regression(distances, speeds, len(distances))
    print('- m:', m, ', c:', c)

    print('Proportional Control Started')    

    while check_state(myTwist) == 0:
        # Read distance and calculate output
        distance = rangefinder.distance()
        new_val = m * distance + c
        # Scale up from predicted value to motor speed
        new_speed = int(new_val * 3)
        
        # Set motor speed
        drivetrain.set_effort(new_speed / 100, new_speed / 100)  # Normalize between -1 to 1
        time.sleep(0.05)

    # Done running; stop motors
    drivetrain.stop()
    print('Proportional Control Stopped')    

# Main Task: monitor buttons for functions
def main():
    reset_twist(myTwist)
    myTwist.set_color(0, 0, 255)
    # Variables to store data
    distances = []
    speeds = []

    # Be sure stopped initially
    drivetrain.stop()
    print('Linear Regression Application:')
    print('- click on the blue button to collect a data point')
    
    while True:
        while (len(distances) < 2):
            if (check_state(myTwist) == 1):
                collect_data(distances, speeds, myTwist)
                reset_twist(myTwist)
                if (len(distances) == 2):
                    print('- twist to blue, then press to collect more data')
                    print('- twist to purple, then press to start proportional control with data collected')
                    state_relation(myTwist)
                else:
                    print('- click on the blue button to collect another data point')
                    myTwist.set_color(0, 0, 255)

        while (len(distances) >= 2):
            if (check_state(myTwist) == 1):
                print(myTwist.get_red())
                collect_data(distances, speeds, myTwist)
                reset_twist(myTwist)
                state_relation(myTwist)
                print('- twist to blue, then press to collect more data')
                print('- twist to purple, then press to start proportional control with data collected')
                
            if (check_state(myTwist) == 2):
                print(myTwist.get_red())
                reset_twist(myTwist)
                exit_relation(myTwist)
                print("- twist to blue to continue collecting data")
                print("- twist to white to reset")
                proportional_control(distances, speeds)
            
            if (check_state(myTwist) == 3):
                reset_twist(myTwist)
                # Reset data
                distances = []
                speeds = []
                myTwist.set_color(0, 0, 255)
                print('Data Reset')
                print('- click on the blue button to collect a data point')
        time.sleep(0.5)
# Run the Main Task
main()
