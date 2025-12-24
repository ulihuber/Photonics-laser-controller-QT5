# Responder simulator for Photonix DP20 Lars232

import serial
import time
import msvcrt
from random import randint



class LaserSim:
    Checksum = 0
    rs232 = 0
    Debug = 0
    Verbose = 0
    DiodeState = 0
    ShutterState = 0
    PockelState = 1
    strCurrent="03e8"
    strCurrentLimit="2222"
    strDiodeVoltage = "3333"
    strDiodeTemp = "00e6"
    strChillerTemp = "0000"
    strShgTemp = "0200"
    strThgTemp = "02c2"
    strFrequency = "000493E0"
    

    def __init__(self):
        self.rs232 = serial.Serial('COM21',19200, timeout=0.1)

    def dprint(self,txt):
        if self.Debug:
            print (txt)
            
    def dprintN(self, txt):
        if self.Debug:
            print (txt, end="")

    def SendWord (self,HexAscii):
        self.dprint("HexAscii in SendWord 1 :")
        self.dprint(HexAscii)
        #self.dprint("Checksum in SendWord 1 :")
        #self.dprint(self.Checksum)
        j = 0
        while j < 4:
            self.rs232.write(HexAscii[j].encode())
            self.rs232.write(HexAscii[j+1].encode())
            self.Checksum += int(HexAscii[j:j+2],16)
            j +=2           #increment by two bytes
        #self.dprintN("Checksum in SendWord 2 :")
        #self.dprint(self.Checksum)

    def SendReply(self,HexAscii):
        self.dprintN("Reply to send: ")
        self.dprint(HexAscii)
        self.rs232.read(1000)   #flush buffer
        self.Checksum = 0
    
        i = 0
        while i < len(HexAscii):
            self.SendWord(HexAscii[i:i+4])
            i +=4           #increment by four bytes (full word)
        self.SendWord(str.format('{:04X}',self.Checksum))
        self.rs232.write(b'\r')

    def sendAck(self, strCommand):
        self.SendReply("01FF" + strCommand + "00")

    def printState(self, command, state):
        onoff = ["Off","Active"]
        print("Kommando: " + command + "=" + onoff[state])    
       

    def ReadCommand(self):
        buf = b''
        while (1):          # wait for line completed
            data = self.rs232.readline()
            if len(data) >0:
                buf += data
                if b'\r' in buf:
                    strTmp = buf.decode().strip(' \t\n\r')
                    buf = b''
                    break

            
        print("")
        self.dprint("in ReadValues")
        self.dprint(strTmp)
       
        self.words = int(strTmp[0:2],16) & 0x0f
        self.dprintN("WordCount = ")
        self.dprint(self.words)
        
        self.command =  strTmp[2:4].upper()
        self.dprintN("Command = ")
        self.dprint(self.command)
      
        werte = list()
        i = 1
        while i <= self.words:
            j = i * 4
            werte.append(strTmp[i*4:i*4+4])
            i += 1

        # set LD    
        if self.command == "00":
            if strTmp[4:8] == "0100":
                self.DiodeState = 1
            else:    
                self.DiodeState = 0
            self.sendAck(self.command)    
            self.printState("Diode",self.DiodeState)
            
        # set shutter
        if self.command == "01":
            if strTmp[4:8] == "0100":
                self.ShutterState = 1
            else:    
                self.ShutterState = 0
            self.sendAck(self.command) 
            self.printState("Shutter",self.ShutterState)
            
        # set pockel
        if self.command == "02":
            if strTmp[4:8] == "0100":
                self.PockelState = 1
            else:    
                self.PockelState = 0
            self.sendAck(self.command) 
            self.printState("Pockel",self.PockelState)

        # Reset
        if self.command == "07":
            self.printState("Reset",1)
            self.DiodeState = 0
            self.ShutterState = 0
            self.PockelState = 1
            strCurrent="03e8"
            time.sleep(0.5)
            self.sendAck(self.command) 
            
        # get state   
        if self.command == "08":
            stateByte = 0xC0 | self.DiodeState | (self.ShutterState <<1) |  (self.PockelState <<2)
            self.SendReply("0188" + str.format('{:02X}',stateByte) + "00")
            print("Laser status sent : " + str.format('{:016b}',stateByte) )
            
        # set current
        if self.command == "09":
            self.strCurrent = strTmp[4:8]
            print ("Current set to " + str.format('{:2.1f}',int(self.strCurrent,16)/100) + " A")
            self.sendAck(self.command)
            
        # get current setting    
        if self.command == "0A":
            self.SendReply("018a" + self.strCurrent)
            print("Laser current setting sent : " + str.format('{:2.1f}',int(self.strCurrent,16)/100) + " A")
            
        # get actual current
        if self.command == "0B":
            self.SendReply("018b" + self.strCurrent)
            print("Actual laser current sent : " + str.format('{:2.1f}',int(self.strCurrent,16)/100) + " A")
            
        # set current limit
        if self.command == "0C":
            self.strCurrentLimit = strTmp[4:8]
            print ("Current limit set to " + str.format('{:2.1f}',int(self.strCurrentLimit,16)/100) + " A")
            self.sendAck(self.command)
            
        # get current limit
        if self.command == "0D":
            self.SendReply("018d" + self.strCurrentLimit)
            print("Current limit sent : " + str.format('{:2.1f}',int(self.strCurrentLimit,16)/100) + " A")
            
        # get diode voltage   
        if self.command == "0E":
            self.SendReply("018e" + self.strDiodeVoltage )
            print("Diode voltage sent : " + str.format('{:2.1f}',int(self.strDiodeVoltageLimit,16)/100) + " A")

        # set frequency
        if self.command == "18":
            self.strFrequency = strTmp[4:12]
            print ("Frequency set to " + str.format('{:6.0f}',int(self.strFrequency,16)/1000) + " kHz")
            self.sendAck(self.command)

        # get frequency
        if self.command == "19":
            self.SendReply("018b" + self.strFrequency)
            print("Actual laser frequency sent : " + str.format('{:6f}',int(self.strFrequency,16)/1000) + " kHz")
         
        # get state2   
        if self.command == "28":
            stateByte = randint(0,0xff)
            self.SendReply("01A8" + str.format('{:02X}',stateByte) + "00")
            print("Laser status sent : " + str.format('{:02X}',stateByte) )
         
        # get error 
        if self.command == "79":
            errs = randint(0,0xffff)
            self.SendReply("02f9" + str.format('{:04X}',errs ))
            print("Error flags sent  : " + str.format('{:016b}',errs ))
            
        # set temperatures
        if self.command == "7B":
            self.strDiodeTemp = strTmp[4:8]
            self.strChillerTemp = strTmp[8:12]
            self.strShgTemp = strTmp[12:16]
            self.strThgTemp = strTmp[16:20]
            print ("Diode temp. set to   " + str.format('{:2.1f}',int(self.strDiodeTemp,16)/10) + " °C")
            print ("Chiller temp. set to " + str.format('{:2.1f}',int(self.strChillerTemp,16)/10) + " °C")
            print ("SHG temp. set to     " + str.format('{:2.1f}',int(self.strShgTemp,16)/10) + " °C")
            print ("THG temp. set to     " + str.format('{:2.1f}',int(self.strThgTemp,16)/10) + " °C")
            self.sendAck(self.command)
            
        # get temperatures
        if self.command == "7D":
            self.SendReply("08fd" + self.strDiodeTemp +self.strChillerTemp + self.strShgTemp + self.strThgTemp + "0000000000000000")
            print("Temperatures sent : " )
            print ("Diode temp.   " + str.format('{:2.1f}',int(self.strDiodeTemp,16)/10) + " °C")
            print ("Chiller temp. " + str.format('{:2.1f}',int(self.strChillerTemp,16)/10) + " °C")
            print ("SHG temp.     " + str.format('{:2.1f}',int(self.strShgTemp,16)/10) + " °C")
            print ("THG temp.     " + str.format('{:2.1f}',int(self.strThgTemp,16)/10) + " °C")

        # get set temperatures
        if self.command == "7C":
            self.SendReply("08fc" + self.strDiodeTemp +self.strChillerTemp + self.strShgTemp + self.strThgTemp + "0000000000000000")
            print("Temperatures sent : " )
            print ("Diode temp.   " + str.format('{:2.1f}',int(self.strDiodeTemp,16)/10) + " °C")
            print ("Chiller temp. " + str.format('{:2.1f}',int(self.strChillerTemp,16)/10) + " °C")
            print ("SHG temp.     " + str.format('{:2.1f}',int(self.strShgTemp,16)/10) + " °C")
            print ("THG temp.     " + str.format('{:2.1f}',int(self.strThgTemp,16)/10) + " °C")

# main function

def main():
    L = LaserSim()
                      
    while(1):
        L.ReadCommand()


if __name__ == '__main__':
  main()
