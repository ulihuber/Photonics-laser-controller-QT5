

err_text = ["Laser Diode temp.    ",
            "Humidity Sensor      ",
            "SHG temp.            ",
            "THG temp.            ",
            "---                  ",
            "---                  ",
            "Laser Crystal temp.  ",
            "Pockel Cell temp.    ",
            "Laser Diode funct.   ",
            "---                  ",
            "---                  ",
            "---                  ",
            "Pockel Cell switch   ",
            "---                  ",
            "Wet Sensor alarm     ",
            "Water Flow           "]
            
err_stat = ["OK","Error"]

state_text = ["Laser Diode   ",
              "Shutter       ",
              "Pockel        ",
              "Keypad        ",
              "---           ",
              "Chiller       ",
              "Laser Enable  ",
              "Key Switch    "]
              
state2_text = ["---           ",
               "---           ",
               "---           ",
               "---           ",             
               "Pockel disable",
               "---           ", 
               "Ext.Frequency ",
               "Ext.Gate      " ]            
              
              # ["Ext.Gate      ",
              # "Ext.Frequency ",
              # "---           ",
              # "Pockel disable",
              # "---           ",
              # "---           ",
              # "---           ",
              # "---           "]              
            

state_stat = ["Off","Active"]

laserProc = [("State",False),("Error",False),("Current",False),("Temperature",False)]
