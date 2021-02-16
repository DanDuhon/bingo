import random
import time
import sys
import os
import shutil
import base64
import subprocess
import _pickle as pickle
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import PIL
from pathlib import Path
from math import ceil


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.buttons = []
        self.create_buttons()
        self.bingoType = None
        self.htmlFile = None
        self.wordsFile = None
        self.pictures = []
        self.bingoPictures = []
        self.historyPictures = []
        self.displayPictures = []
        self.words = []
        self.calledItems = []
        self.xOffset = 0
        self.yOffset = 0
        self.startText = canvas.create_text(10, 10, text=startText, font=("calibri", 16), anchor=tk.NW)
        self.gameInProgress = False
        self.historyImages = []
        self.historyCanvas = []
        
        self.wBindId = self.enable_binding("w", self.ctrl_w)
        self.pBindId = self.enable_binding("p", self.ctrl_p)
        self.qBindId = self.enable_binding("q", self.ctrl_q)
        self.oBindId = self.enable_binding("o", self.ctrl_o)
        self.nBindId = self.enable_binding("n", self.ctrl_n)
        self.vBindId = self.enable_binding("v", self.ctrl_v)

        self.disable_binding("n", self.nBindId)
        self.disable_binding("v", self.vBindId)

        # Find all the .bingo files and associated folders that are stored in the dict
        # and delete one if the other doesn't exist.
        keysToDelete = []
        for k, v in fileFolderDict.items():
            if not os.path.exists(k) or not os.path.exists(v):
                if os.path.exists(k):
                    os.remove(k)
                if os.path.exists(v):
                    shutil.rmtree(v)

                keysToDelete.append(k)

        for k in keysToDelete:
            del fileFolderDict[k]
            
        with open("fileFolderDict.p", "wb") as f:
            pickler = pickle.Pickler(f)
            pickler.dump(fileFolderDict)
        

    # Generates an HTML table representation of the bingo card for pictures
    def generate_table(self, cols, rows, freeSpace, pagebreak = True):
        if self.bingoType == "pictures":
            ps = random.sample(self.bingoPictures, cols * rows)
        elif self.bingoType == "words":
            ps = random.sample(self.words, cols * rows)
            
        if pagebreak:
            res = "<table class=\"newpage\">\n"
        else:
            res = "<table>\n"
            
        for i, item in enumerate(ps):
            if i % cols == 0:
                res += "\t<tr>\n"
                
            if i == 12 and freeSpace:
                res += "\r\<td>FREE SPACE</td>\n"
            elif self.bingoType == "pictures":
                res += "\t\t<td><img src=\"data:image/png;base64,{0}\"></td>\n".format(base64.b64encode(open(item, "rb").read()).decode("utf-8"))
            elif self.bingoType == "words":
                res += "\t\t<td>" + item + "</td>\n"
                
            if i % cols == cols - 1:
                res += "\t</tr>\n"
                
        res += "</table>\n"
        
        return res

    # Resizes an image based on parameters
    def resize_image(self, folder, destFolder, picture, pictureNum, pictureType, maxSideSize):
        try:
            img = Image.open(folder + "/" + picture)
            if img.size[0] >= img.size[1]:
                wSize = maxSideSize
                wPct = (wSize / float(img.size[0]))
                hSize = int((float(img.size[1]) * float(wPct)))
            else:
                hSize = maxSideSize
                hPct = (hSize / float(img.size[1]))
                wSize = int((float(img.size[0]) * float(hPct)))
                
            img = img.resize((wSize, hSize), Image.ANTIALIAS)

            resizedFileName = destFolder + "/" + str(pictureNum) + "_" + pictureType + os.path.splitext(folder + "/" + picture)[1]
            img.save(resizedFileName)
            return resizedFileName
        except PIL.UnidentifiedImageError:
            self.popup_message(picture + " is not a recognized image format!\r\nPlease make sure your BINGO images folder has ONLY images in it!")
            return None
        except:
            raise


    def save_bingo_file(self):
        output = filedialog.asksaveasfile(mode="w", initialdir=os.getcwd(), defaultextension=".bingo")
        if not output:
            return

        # Update the dict that tracks all file locations for this bingo game.
        fileFolderDict[output.name] = os.getcwd() + "//working_dir//" + os.path.splitext(os.path.basename(output.name))[0]
        with open("fileFolderDict.p", "wb") as f:
            pickler = pickle.Pickler(f)
            pickler.dump(fileFolderDict)

        pickler = open(output.name, "wb")

        pickleDict = {
            "html": self.htmlFile,
            "words": self.words,
            "historyPictures": self.historyPictures,
            "displayPictures": self.displayPictures
            }

        pickle.dump(pickleDict, pickler, -1)

        pickler.close()

        return output.name


    def save_dict_file(self, bingoName):
        pickler = open(bingoName, "wb")

        pickleDict = {
            "html": self.htmlFile,
            "words": self.words,
            "historyPictures": self.historyPictures,
            "displayPictures": self.displayPictures
            }

        pickle.dump(pickleDict, pickler, -1)

        pickler.close()


    def load_file(self):
        loadFile = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select BINGO file to open", filetypes = [("BINGO files", ".bingo")])
        if not loadFile:
            return False

        pickler = open(loadFile, "rb")
        pickleDict = pickle.load(pickler)
        pickler.close()

        self.htmlFile = pickleDict["html"]
        self.words = pickleDict["words"]
        self.historyPictures = pickleDict["historyPictures"]
        self.displayPictures = pickleDict["displayPictures"]

        if self.words:
            self.bingoType = "words"
        elif self.displayPictures:
            self.bingoType = "pictures"

        return True


    def interrupt_confirm(self):
        if self.gameInProgress:
            self.popup_confirm()
            interrupt = self.interrupt_value()

            if not interrupt:
                return False
            else:
                return True

        return True


    def reset(self):
        canvas.delete("all")
        
        if self.historyImages:
            for i in self.historyImages:
                i.place_forget()
                
        self.startText = canvas.create_text(10, 10, text=startText, font=("calibri", 16), anchor=tk.NW)
        self.bingoType = None
        self.htmlFile = None
        self.wordsFile = None
        self.pictures = []
        self.bingoPictures = []
        self.historyPictures = []
        self.displayPictures = []
        self.words = []
        self.calledItems = []
        self.xOffset = 0
        self.yOffset = 0
        self.gameInProgress = False
        self.historyImages = []

        self.nextImage["state"] = tk.DISABLED

        fileMenu.entryconfig("View BINGO Cards", state=tk.DISABLED)
        fileMenu.entryconfig("Display next image/word", state=tk.DISABLED)
        
        self.wBindId = self.enable_binding("w", self.ctrl_w)
        self.pBindId = self.enable_binding("p", self.ctrl_p)
        self.qBindId = self.enable_binding("q", self.ctrl_q)
        self.oBindId = self.enable_binding("o", self.ctrl_o)
        self.nBindId = self.enable_binding("n", self.ctrl_n)
        self.vBindId = self.enable_binding("v", self.ctrl_v)

        self.disable_binding("n", self.nBindId)
        self.disable_binding("v", self.vBindId)


    def check_number_of_items(self):
        if self.bingoType == "pictures":
            while True:
                folder = filedialog.askdirectory(title="Select the folders the pictures are in.")
                if not folder:
                    return False

                self.pictures = [file for file in os.listdir(folder) if os.path.isfile(os.path.join(folder, file)) and file[-5:] != ".html"]

                if len(self.pictures) < 25:
                    self.popup_message("Your folder needs to have at least 25 pictures in it!")
                    continue
                elif len(self.pictures) > 95:
                    self.popup_message("Sorry, this program can only handle up to 95 pictures.\r\nPlease remove some images from the folder and try again.")
                    continue
                
                break

            return folder
        elif self.bingoType == "words":
            while True:
                file = filedialog.askopenfilename(title="Select the file the words are in.", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
                if not file:
                    return False

                f = open(file, "r").readlines()

                self.words = list(set([word.replace("\r", "").replace("\n", "") for word in f]))
                              
                if len(self.words) < 25:
                    self.popup_message("Your words file must have at least 25 unique words in it (one word per line)!")
                    continue
                elif len(self.words) > 105:
                    self.popup_message("Sorry, this program can only handle up to 105 words.\r\nPlease remove some words from the file and try again.")
                    continue
                
                break

            return file


    def get_number_of_cards(self):
        while True:
            self.popup_cards()
            
            try:
                cards = int(self.cards_value())
            except ValueError:
                self.popup_message("It has to be a positive whole number!")
                continue
            except:
                raise

            if cards <= 0:
                self.popup_message("You need at least one card!")
                continue

            break

        return cards


    def create_bingo_cards(self, freeSpace, cards, outFile):
        columns = 5
        rows = 5

        for c in range(cards):
            random.shuffle(self.pictures)
            random.shuffle(self.words)
            if c == cards + 1:
                outFile.write(self.generate_table(columns, rows, freeSpace, pagebreak=True))
            else:
                outFile.write(self.generate_table(columns, rows, freeSpace, pagebreak=False))


    def generate_bingo_cards(self, bingoType):
        if not self.interrupt_confirm():
            return

        self.reset()

        self.bingoType = bingoType

        items = self.check_number_of_items()

        if not items:
            self.reset()
            return

        self.popup_message("Now save the BINGO file for this game.")

        dest = self.save_bingo_file()

        if not dest:
            self.reset()
            return

        workingDirName = os.path.splitext(os.path.basename(dest))[0]
        bingoFullPath = os.getcwd() + "\\working_dir\\" + workingDirName

        if os.path.exists(bingoFullPath):
            shutil.rmtree(bingoFullPath)

        if not os.path.exists(bingoFullPath):
            os.makedirs(bingoFullPath)

        self.gameInProgress = False
        self.nextImage["state"] = tk.DISABLED

        cards = self.get_number_of_cards()
            
        self.popup_free_space()
        freeSpace = self.free_space_value()

        if self.bingoType == "pictures":
            self.progressLabel = tk.Label(root, text="Processing images...")
            self.progressLabel.place(x=450, y=530)
            self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=len(self.pictures), mode="determinate")
            self.progress.place(x=450,y=550)
            
            for i, picture in enumerate(self.pictures):
                self.progress["value"] = i + 1
                root.update_idletasks()
                newBingoPicture = self.resize_image(items, bingoFullPath, picture, i, "bingo", 75)
                if not newBingoPicture:
                    self.reset()
                    return
                
                self.bingoPictures.append(newBingoPicture)
                
                newHistoryPicture = self.resize_image(items, bingoFullPath, picture, i, "history", 50)
                if not newHistoryPicture:
                    self.reset()
                    return
                
                self.historyPictures.append(newHistoryPicture)
                
                newDisplayPicture = self.resize_image(items, bingoFullPath, picture, i, "display", 350)
                if not newDisplayPicture:
                    self.reset()
                    return
                
                self.displayPictures.append(newDisplayPicture)

            self.progress.place_forget()
            self.progressLabel.place_forget()

        self.htmlFile = bingoFullPath + "\\" + "bingo_cards.html"
        outFile = open(self.htmlFile, "w")
        outFile.write(head)

        self.create_bingo_cards(freeSpace, cards, outFile)

        outFile.write("</body></html>")
        outFile.close()

        # Since these pictures are embedded in the HTML file, we don't need to keep them.
        for file in self.bingoPictures:
            os.remove(file)

        self.save_dict_file(dest)

        self.prep_for_play()
        

    def prep_for_play(self):
        random.shuffle(self.displayPictures)
        random.shuffle(self.words)
        
        self.nextImage["state"] = tk.NORMAL

        fileMenu.entryconfig("View BINGO Cards", state=tk.NORMAL)
        fileMenu.entryconfig("Display next image/word", state=tk.NORMAL)
        
        self.nBindId = self.enable_binding("n", self.ctrl_n)
        self.vBindId = self.enable_binding("v", self.ctrl_v)


    def play_bingo(self):
        if not self.interrupt_confirm():
            return

        self.reset()

        if not self.load_file():
            return

        self.prep_for_play()


    def display_next_image_or_word(self):
        self.gameInProgress = True
        
        if self.startText:
            canvas.delete(self.startText)

        if self.bingoType == "pictures":
            items = self.displayPictures
            
            # Display the next image
            self.calledItems.append(self.displayPictures.pop(0))
            img = ImageTk.PhotoImage(Image.open(self.calledItems[-1]))
            if len(self.calledItems) > 1:
                canvas.delete(self.displayCanvas)
            self.displayCanvas = canvas.create_image(500, 625, anchor=tk.S, image=img)
            canvas.image = img

            # Put the called images into the history
            hImg = ImageTk.PhotoImage(Image.open(self.calledItems[-1].replace("_display.", "_history.")))
            hi = tk.Label(image=hImg)
            hi.image = hImg
            hi.place(x=5 + self.xOffset, y=10 + self.yOffset)
            self.historyImages.append(hi)
            self.xOffset += 52

            if len(self.calledItems) % 19 == 0:
                self.yOffset += 50
                self.xOffset = 0
        elif self.bingoType == "words":
            items = self.words
            
            # Display the next word
            self.calledItems.append(self.words.pop(0))
            if len(self.calledItems) > 1:
                canvas.delete(self.displayCanvas)
            self.displayCanvas = canvas.create_text(500, 500, text=self.calledItems[-1], font=("calibri", 40), anchor=tk.S)

            # Put the called word into the history
            for hc in self.historyCanvas:
                canvas.delete(hc)

            self.historyCanvas = []

            for x in range(ceil(len(self.calledItems) / 15)):
                xCoord = (10 if x == 0 else x * 150)
                self.historyCanvas.append(canvas.create_text(xCoord, 10, text="\n".join(self.calledItems[x * 15:min([(x + 1) * 15, len(self.calledItems)])]), font=("calibri", 14), anchor=tk.NW))

        if len(items) == 0:
            self.disable_binding("n", self.nBindId)
            self.nextImage["state"] = tk.DISABLED
            fileMenu.entryconfig("Display next image/word", state=tk.DISABLED)
            self.popup_message("That's all the " + self.bingoType + ". Someone better have a BINGO by now!")
            self.gameInProgress = False
            return


    def view_bingo_cards(self):
        try:
            os.startfile(self.htmlFile)
        except AttributeError:
            try:
                subprocess.call(["open", self.htmlFile])
            except:
                popup_message("Couldn't open the file.\r\nYour BINGO cards file is\r\n" + self.htmlFile)
                

    def create_buttons(self):
        self.nextImage = tk.Button(self)
        self.nextImage["text"] = "Display the next image/word"
        self.nextImage["font"] = ("calibri", 16)
        self.nextImage["command"] = self.display_next_image_or_word
        self.nextImage.pack({"side": "left"})
        self.nextImage["state"] = tk.DISABLED
        self.buttons.append(self.nextImage)
        

    def popup_confirm(self):
        self.cn = popupWindow(self.master, "Do you really want to stop this game?", button1Text="Yes", button2Text="No")
        for b in self.buttons:
            b["state"] = tk.DISABLED

        menuBar.entryconfig("File", state=tk.DISABLED)
            
        self.master.wait_window(self.cn.top)
        for b in self.buttons:
            b["state"] = tk.NORMAL

        menuBar.entryconfig("File", state="normal")
        

    def popup_free_space(self):
        self.fs = popupWindow(self.master, "Do want a free space in the middle square?", button1Text="Yes", button2Text="No")
        for b in self.buttons:
            b["state"] = tk.DISABLED

        menuBar.entryconfig("File", state=tk.DISABLED)
            
        self.master.wait_window(self.fs.top)
        for b in self.buttons:
            if b == self.nextImage:
                continue
            
            b["state"] = tk.NORMAL

        menuBar.entryconfig("File", state="normal")
        

    def popup_cards(self):
        self.c = popupWindow(self.master, "Enter the number of BINGO cards to generate.", entry=True, button1Text="Ok")
        for b in self.buttons:
            b["state"] = tk.DISABLED

        menuBar.entryconfig("File", state=tk.DISABLED)
            
        self.master.wait_window(self.c.top)
        for b in self.buttons:
            if b == self.nextImage:
                continue
            
            b["state"] = tk.NORMAL

        menuBar.entryconfig("File", state="normal")
        

    def popup_message(self, message):
        self.w = popupWindow(self.master, message, button1Text="Ok")
        for b in self.buttons:
            b["state"] = tk.DISABLED

        menuBar.entryconfig("File", state=tk.DISABLED)
            
        self.master.wait_window(self.w.top)
        for b in self.buttons:
            if b == self.nextImage:
                continue
            
            b["state"] = tk.NORMAL

        menuBar.entryconfig("File", state="normal")
        

    def free_space_value(self):
        return self.fs.value
        

    def cards_value(self):
        return self.c.value


    def interrupt_value(self):
        return self.cn.value


    def ctrl_w(self, event):
        self.generate_bingo_cards("words")


    def ctrl_p(self, event):
        self.generate_bingo_cards("pictures")


    def ctrl_v(self, event):
        self.view_bingo_cards()


    def ctrl_o(self, event):
        self.play_bingo()


    def ctrl_q(self, event):
        root.quit()


    def ctrl_n(self, event):
        self.display_next_image_or_word()


    def disable_binding(self, bindKey, bindId):
        self.unbind("<" + bindKey + ">", bindId)


    def enable_binding(self, bindKey, method):
        return self.bind_all("<Control-" + bindKey + ">", method)
    

class popupWindow(object):
    def __init__(self, master, labelText, entry=False, button1Text=None, button2Text=None):
        top = self.top = tk.Toplevel(master)
        self.l = tk.Label(top, text=labelText, font=("calibri", 16))
        self.l.pack()

        if entry:
            self.e = tk.Entry(top, font=("calibri", 16))
            self.e.pack()

        if button1Text:
            if entry:
                self.b1 = tk.Button(top, text=button1Text, font=("calibri", 16), command=self.cleanupEntry)
            else:
                self.b1 = tk.Button(top, text=button1Text, font=("calibri", 16), command=self.cleanupYes)

            self.b1.pack()

        if button2Text:
            self.b2 = tk.Button(top, text=button2Text, font=("calibri", 16), command=self.cleanupNo)
            self.b2.pack()
        
        
    def cleanupYes(self):
        self.value = True
        self.top.destroy()
        
        
    def cleanupNo(self):
        self.value = False
        self.top.destroy()

        
    def cleanupEntry(self):
        self.value = self.e.get()
        self.top.destroy()


fileFolderDict = {}

if not os.path.exists(os.getcwd() + "//working_dir"):
    os.makedirs("working_dir")

if not os.path.exists(os.getcwd() + "//fileFolderDict.p"):
    pickle.dump(fileFolderDict, open(os.getcwd() + "//fileFolderDict.p", "wb"), -1)

if os.path.getsize("fileFolderDict.p") > 0:
    with open("fileFolderDict.p", "rb") as f:
        unpickler = pickle.Unpickler(f)
        fileFolderDict = unpickler.load()

print(fileFolderDict)

startText = """BINGO creator/player

To create BINGO cards:
1. Setup
    a. Word BINGO - create a file with a word on each line (25-105 words).
    b. Picture BINGO - Put your BINGO images into a folder with nothing else in it (25-95 images).
2. Click File --> New... --> select which kind of BINGO cards you want.
    a. Word BINGO - Select the file that contains the BINGO words (min 25, max 105).
    b. Picture BINGO - Select the folder with your BINGO images in it.
3. Follow remaining instructions.

To play BINGO:
1. Click File --> Load BINGO button.
2. Open a .bingo file you created in create steps above.
3. Click the \"Display next image/word\" button until someone wins!"""
            
head = ("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\" \"http://www.w3.org/TR/html4/strict.dtd\">\n"
        "<html lang=\"en\">\n<head>\n"
        "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
        "<title>Bingo Cards</title>\n"
        "<style type=\"text/css\">\n"
        "\tbody { font-size: 14px; }\n"
        "\ttable { margin: 40px auto; border-spacing: 2px; }\n"
        "\t.newpage { page-break-after:always; }\n"
        "\ttr { height: 80px; }\n"
        "\ttd { text-align: center; border: thin black solid; padding: 10px; width: 80px; }\n"
        "</style>\n</head>\n<body>\n")

root = tk.Tk()
canvas = tk.Canvas(root, width = 1000, height = 615)
canvas.pack()
root.resizable(False, False)
app = Application(master=root)
menuBar = tk.Menu(root)
fileMenu = tk.Menu(menuBar, tearoff=0)
newMenu = tk.Menu(fileMenu, tearoff=0)
fileMenu.add_cascade(label="New...", menu=newMenu)
newMenu.add_command(label="Word BINGO Cards", command=lambda: app.generate_bingo_cards("words"), accelerator="Ctrl+W")
newMenu.add_command(label="Picture BINGO Cards", command=lambda:app.generate_bingo_cards("pictures"), accelerator="Ctrl+P")
fileMenu.add_command(label="Load BINGO File", command=app.play_bingo, accelerator="Ctrl+O")
fileMenu.add_command(label="View BINGO Cards", command=app.view_bingo_cards, state=tk.DISABLED, accelerator="Ctrl+V")
fileMenu.add_command(label="Display next image/word", command=lambda: app.display_next_image_or_word(), state=tk.DISABLED, accelerator="Ctrl+N")
fileMenu.add_separator()
fileMenu.add_command(label="Quit", command=root.quit, accelerator="Ctrl+Q")
menuBar.add_cascade(label="File", menu=fileMenu)

root.config(menu=menuBar)
app.mainloop()
root.destroy()
