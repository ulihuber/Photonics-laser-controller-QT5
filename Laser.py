#Control library for Photonix DP20 Lars232
# displays laser state and errors
# avtivates diode, shutter and pockel

from serial import Serial, SerialException
from serial.tools.list_ports import comports
import time
import laserconstants as const


class Laser():
    def __init__(self, findCom = True, com = "", verbose = False, debug = False):
        Checksum = 0
        self.Debug = debug
        self.Verbose = verbose
        if findCom:
            self.rs232 = ""
            if self.checkLaserPort():
                print("Port OK")
            else:
                print("No Laser!")
        else:
            self.rs232 = Serial(com,19200, timeout=0.1)
        #self.rs232 = serial.Serial('/dev/ttyAMA0',19200, timeout=0.1)
        #self.rs232 = serial.Serial('/dev/ttyUSB0',19200, timeout=0.1)
        
    def checkLaserPort(self):
      ports = comports()
      for port in ports:
         comPort = port.device
         print("Test ",comPort + ": ", end='')
         try:
            self.rs232 = Serial(comPort,19200, timeout=0.5)
            self.rs232.read(1000) #flush buffer
            resetCommand = "010700000008"
            for c in resetCommand:
               #print(c, end='')
               self.rs232.write(c.encode())
            self.rs232.write(b'\r')
            time.sleep(.500)
            data = self.rs232.readline()
            print(data)
            if data.decode() == "01FF07000107\r":
               return True         
         except (OSError, SerialException):
            print("Port not available")
            continue
         print("No Laser connected")
         self.rs232.close()
         continue 
      return False       
        


    def SendCommand (self,HexAscii, commandText, itemSize=1):
        if self.Debug:
            print("\n"+commandText)
            print("Kommando: ", HexAscii + " ",end='')
        self.rs232.read(1000) #flush buffer
        Checksum = 0
        i = 0
        while i < len(HexAscii):
            self.rs232.write(HexAscii[i].encode())
            self.rs232.write(HexAscii[i+1].encode())
            Checksum += int(HexAscii[i:i+2],16)
            i += 2
        if self.Debug:
            print( str.format('{:04X}',Checksum))
        strChecksum = str.format('{:04X}',Checksum)
        self.rs232.write(strChecksum[0:2].encode()) 
        self.rs232.write(strChecksum[2:4].encode()) 
        self.rs232.write(b'\r')
        time.sleep(.200)
        return self.ReadValues(item_len = itemSize)
        


    def Switch(self,command, state):
        commands = {"Diode":"0100", "Shutter":"0101","Pockel":"0102","Reset":"0107"}
        onoff = ["Off","Active"]
        self.SendCommand(commands[command]+"0"+str(state)+"00", "Switch " + command , itemSize = 1)

    def ReadReply(self):
        buf = b''
        while (1):
            data = self.rs232.readline()
            if len(data) > 0 and  self.Debug:
                print("Rohdaten: ", data.decode())
            if len(data) > 0:
                buf += data
                if b'\r' in buf:
                    line = buf.decode().strip(' \t\n\r')
                    buf = b''
                    break
        return line


    def ReadValues(self,item_len=1):
        strTmp = self.ReadReply()
        item_count = int(strTmp[0:2])
        werte = list()
        i = 0
        while i < item_count:
            value_str = strTmp[4 + i*2*item_len : 4 + i*2*item_len + 2*item_len]
            value = int(value_str,16)
            #print ("ReadValues: ", value_str, value)
            werte.append(value)
            i += 1
        return werte

    def GetStates(self):
        flags = self.SendCommand("0008", "Get states", itemSize = 1)
        #flags = self.ReadValues(item_len = 1)

        if self.Verbose:
            print("States")
            i = 0
            while i < 8:
                print(const.state_text[i],end='')
                print(const.state_stat[ ((flags[0] & (1<<i))!=0)])  #pick state text from bit state
                i +=1
            print()    
        return flags[0]

    def GetStates2(self):
        flags = self.SendCommand("0028", "Get states 2", itemSize = 1)

        #flags = self.ReadValues(item_len = 1)
        #print(str.format('{:04X}',flags[0]))

        if self.Verbose:
            print("PockelStates")
            i = 0
            while i < 8:
                print(const.state2_text[i],end='')
                print(const.state_stat[ ((flags[0] & (1<<i))!=0)])  #pick state text from bit state
                i +=1  
            print()
        return flags[0]


    def GetErrors(self):
        flags = self.SendCommand("0079", "Get Errors", itemSize = 2)
        #flags = self.ReadValues(item_len = 2)
        if self.Verbose:        #if (flags[0] != 0) and self.Verbose:
            print("Errors")
            i = 0
            while i < 16:
                print(const.err_text[i],end='')
                print(const.state_stat[ ((flags[0] & (1<<i))!=0)])  #pick state text from bit state
                i +=1  
            #i = 0
            # while i < 16:
                # print(i,end='')
                # print(const.state_stat[ ((flags[1] & (1<<i))!=0)])  #pick state text from bit state
                # i +=1      
            # print()               

        return flags[0]

    def GetValues (self,command, commandText, header, item_text, item_len, item_sign, divisor):
        int_values = self.SendCommand(command, commandText, itemSize = item_len)
        #int_values = self.ReadValues(item_len)
        if self.Verbose:
            print ("\n\r" + header)
        values = []
        i = 0
        for text in item_text:
            values.append(int_values[i]/divisor)
            if self.Verbose:
                print(text + " " + str(int_values[i]/divisor) + " " + item_sign)
            i += 1
        if self.Verbose:
            print()
        print("GetValues: ",values)
        return values

    def GetCurrent(self):
        current = self.GetValues(command = "000B",
                        commandText = "Get current",
                        header = "Actual current",
                        item_text = ["Diode"],
                        item_len = 2,
                        item_sign = "A",
                        divisor = 100)
        return float(current[0])

    def SetCurrent(self,current):
        self.SendCommand("0109"+ str.format('{:04X}',int(current)*100), "Set current", itemSize = 1)
        print("Current set to: " + str(current) + " A")
        #int_values = self.ReadValues(item_len = 1) 

    def GetFrequency(self):
        frequency = self.GetValues(command = "0019",
                                   commandText = "Get frequency",
                                   header = "Frequency",
                                   item_text = ["Intern"],
                                   item_len = 4,
                                   item_sign = "Hz",
                                   divisor = 1)
                           
        return int(frequency[0])


    def SetFrequency(self,frequency):
        self.SendCommand("0218"+ str.format('{:08X}',int(frequency * 1000)), "Set frequency", itemSize = 1)
        print("Frequency set: " + str(frequency) + " Hz")

    def GetTemps(self):
        temps = self.GetValues(command = "007D",
                                commandText = "Get act. temperatures",
                                header = "Act.Temperatures",
                                item_text =  ["Diode   : ",
                                              "Chiller : ",
                                              "SHG     : ",
                                              "THG     : ",
                                              #"T1      : ",
                                              #"T2      : ",
                                              #"T3      : ",
                                              #"T4      : "
                                              ],
                                item_len = 2,
                                item_sign = "°C",
                                divisor = 10)
        temps.remove(temps[1])
        return temps
        
    def GetTempSet(self):
        temps = self.GetValues(command = "007C",
                                commandText = "Get set. temperatures",
                                header = "Set.Temperatures",
                                item_text =  ["Diode   : ",
                                              "Chiller : ",
                                              "SHG     : ",
                                              "THG     : ",
                                              #"T1      : ",
                                              #"T2      : ",
                                              #"T3      : ",
                                              #"T4      : "
                                              ],
                                item_len = 2,
                                item_sign = "°C",
                                divisor = 10)
        temps.remove(temps[1])
        return temps    
        
        
    def SetTemps(self):
        self.SendCommand("087B"+
                          str.format('{:04X}', 210)+
                          str.format('{:04X}', 275)+
                          str.format('{:04X}', 497)+
                          str.format('{:04X}', 703)+
                          str.format('{:04X}', 500)+
                          str.format('{:04X}', 500)+
                          str.format('{:04X}', 250)+
                          str.format('{:04X}', 250), "Set temperatures", itemSize = 1)
        #int_values = self.ReadValues(item_len = 1)                  

        

 # main function
#
def main():
    L = Laser()
    #test = L.GetStates()



if __name__ == '__main__':
  main()
