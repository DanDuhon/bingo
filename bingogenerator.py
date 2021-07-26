def log_status(status, writeType="a"):
    """
    Logs events to a log file.

    Required Parameters:
        status: String
            The text to write in the log file.

    Optional Parameters:
        writeType: String
            The write type with which to open the file.
            Default: "a" (append)
    """
    logFile = open("log.txt", writeType)
    logFile.write(str(datetime.datetime.now()) + ": " + status + "\n")
    logFile.close()


try:
    import random
    import datetime
    import sys
    import os
    import shutil
    import base64
    import imgkit
    import webbrowser
    import _pickle as pickle
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk
    from PIL import Image, ImageTk
    import PIL
    from math import ceil


    class Application(tk.Frame):
        def __init__(self, master=None):
            log_status("Initiating application.")
            tk.Frame.__init__(self, master)
            self.pack()
            self.buttons = []
            self.create_buttons()
            self.bingoFullPath = None
            self.bingoType = None
            self.wordsFile = None
            self.pictures = []
            self.bingoCards = []
            self.cardPictures = []
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

            # Create the keyboard shortcuts.
            self.wBindId = self.enable_binding("w", self.ctrl_w)
            self.pBindId = self.enable_binding("p", self.ctrl_p)
            self.qBindId = self.enable_binding("q", self.ctrl_q)
            self.oBindId = self.enable_binding("o", self.ctrl_o)
            self.nBindId = self.enable_binding("n", self.ctrl_n)
            self.dBindId = self.enable_binding("d", self.ctrl_d)
            self.cBindId = self.enable_binding("c", self.ctrl_c)

            # Disable these because they are only valid when a .bingo file has been loaded.
            self.disable_binding("d", self.dBindId)
            self.disable_binding("c", self.cBindId)

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

            # Save the dictionary in case there were any changes.
            with open("fileFolderDict.p", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(fileFolderDict)
            

        def generate_html_card(self, cardNum, cols, rows, freeSpace):
            """
            Generates an HTML file of the bingo card.
            Then converts the HTML file into an image.

            Required Parameters:
                cardNum: Integer
                    The number of this card, used to generate distinct file names.
                    
                cols: Integer
                    The number of columns in the table.

                rows: Integer
                    The number of rows in the table.

                freeSpace: Boolean
                    Whether there is a "free space" in the center square of the table.
            """
            log_status("Start of generate_html_card: cols=" + str(cols) + ", rows=" + str(rows) + ", freeSpace=" + str(freeSpace))
            # Get a random sample of the words/pictures with which to fill in this card.
            if self.bingoType == "pictures":
                ps = random.sample(self.cardPictures, cols * rows)
            elif self.bingoType == "words":
                ps = random.sample(self.words, cols * rows)
                
            res = "<table>\n"
                
            for i, item in enumerate(ps):
                if i % cols == 0:
                    res += "\t<tr>\n"
                    
                if i == 12 and freeSpace:
                    res += "\r\<td>FREE SPACE</td>\n"
                elif self.bingoType == "pictures":
                    # Embed the picture in the HTML file so it can be opened without the picture files existing.
                    res += "\t\t<td><img src=\"data:image/png;base64,{0}\"></td>\n".format(base64.b64encode(open(item, "rb").read()).decode("utf-8"))
                elif self.bingoType == "words":
                    res += "\t\t<td>" + item + "</td>\n"
                    
                if i % cols == cols - 1:
                    res += "\t</tr>\n"
                    
            res += "</table>\n"

            # Save the HTML file.
            self.htmlFile = self.bingoFullPath + "\\" + "bingo_card.html"
            outFile = open(self.htmlFile, "w")
            outFile.write(head)
            outFile.write(res)
            outFile.write(tail)
            outFile.close()

            # Convert the HTML file to an image.
            imgkit.from_file(self.bingoFullPath + "\\" + "bingo_card.html", self.bingoFullPath + "\\bingo_cards\\bingo_card_" + str(cardNum) + ".jpg", config=config)

            # Delete the HTML file.
            os.remove(self.bingoFullPath + "\\" + "bingo_card.html")

            # Add the location of the image to what will be saved in the .bingo file.
            self.bingoCards.append(self.bingoFullPath + "\\bingo_cards\\bingo_card_" + str(cardNum) + ".jpg")


        def open_bingo_cards_folder(self):
            webbrowser.open(os.path.realpath(self.bingoFullPath + "\\bingo_cards\\"))


        # Resizes an image based on parameters
        def resize_image(self, folder, destFolder, picture, pictureNum, pictureType, maxSideSize):
            """
            Resizes an image and saves it as a new file.
            Returns a String of the full path of the resized image file.

            Required Parameters:
                folder: String
                    The folder path for the images.

                destFolder: String
                    Where the resized image will be saved.

                picture: String
                    The file name of the image to be resized.

                pictureNum: Integer
                    The index of this image in the file list in the folder.

                pictureType: String
                    The type of image, which determines file naming.

                maxSideSize: Integer
                    The length in pixels of the longest side of the resized image.
            """
            log_status("Start of resize_image: folder=" + folder + ", destFolder=" + destFolder + ", picture=" + picture + ", pictureNum=" + str(pictureNum) + ", maxSideSize=" + str(maxSideSize))
            try:
                img = Image.open(folder + "/" + picture)
                # See whether the height or width of the image is larger.
                # The larger side is scaled to the maxSideSize.
                # The smaller side is scaled based on the percent change of the larger side.
                if img.size[0] >= img.size[1]:
                    wSize = maxSideSize
                    wPct = (wSize / float(img.size[0]))
                    hSize = int((float(img.size[1]) * float(wPct)))
                else:
                    hSize = maxSideSize
                    hPct = (hSize / float(img.size[1]))
                    wSize = int((float(img.size[0]) * float(hPct)))
                    
                img = img.resize((wSize, hSize), Image.ANTIALIAS)

                # Save the resized image in this game's folder.
                resizedFileName = destFolder + "/" + pictureType + "_pictures/" + str(pictureNum) + "_" + pictureType + os.path.splitext(folder + "/" + picture)[1]
                img.save(resizedFileName)
                
                log_status("    Returning " + resizedFileName)
                return resizedFileName
            except PIL.UnidentifiedImageError:
                self.popup(picture + " is not a recognized image format!\r\nPlease make sure your Bingo images folder has ONLY images in it!", button1Text="Ok")
                log_status("    Returning None")
                return None
            except:
                raise


        def save_bingo_file(self):
            """
            Saves a .bingo file so this game can be loaded later.
            Returns a String containing the file name.
            """
            log_status("Start of save_bingo_file.")
            # Prompt the user to save the .bingo file.
            output = filedialog.asksaveasfile(mode="w", initialdir=os.getcwd(), defaultextension=".bingo")

            if not output:
                return

            # Update the dict that tracks all file locations for this bingo game.
            fileFolderDict[output.name] = os.path.dirname(__file__) + "//working_dir//" + os.path.splitext(os.path.basename(output.name))[0]
            with open("fileFolderDict.p", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(fileFolderDict)

            # Update the dict that tracks all file locations for this bingo game.
            self.save_dict_file(output.name)

            log_status("    Returning " + output.name)
            return output.name


        def save_dict_file(self, bingoName):
            """
            Saves data on file locations to a .bingo file.

            Required Parameters:
                bingoName: String
                    The file name of the .bingo file.
            """
            log_status("Start of save_dict_file: bingoName=" + bingoName)
            # Save the dict for this Bingo game that tracks locations of files.
            pickler = open(bingoName, "wb")

            pickleDict = {
                "bingoCards": self.bingoCards,
                "words": self.words,
                "historyPictures": self.historyPictures,
                "displayPictures": self.displayPictures,
                "workLocation": self.bingoFullPath
                }

            pickle.dump(pickleDict, pickler, -1)

            pickler.close()


        def load_file(self):
            """
            Loads a .bingo file and sets the following variables in the Application:
                self.bingoCards
                self.words
                self.historyPictures
                self.displayPictures
                self.bingoType
                self.bingoFullPath
            """
            log_status("Start of load_file.")
            # Prompt the user for a .bingo file to load.
            loadFile = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Bingo file to open", filetypes = [("Bingo files", ".bingo")])
            if not loadFile:
                return False

            pickler = open(loadFile, "rb")
            pickleDict = pickle.load(pickler)
            pickler.close()

            # Set variables from the pickled dict.
            self.bingoCards = pickleDict["bingoCards"]
            self.words = pickleDict["words"]
            self.historyPictures = pickleDict["historyPictures"]
            self.displayPictures = pickleDict["displayPictures"]
            self.bingoFullPath = pickleDict["workLocation"]

            if self.words:
                self.bingoType = "words"
            elif self.displayPictures:
                self.bingoType = "pictures"

            log_status("    Returning True")
            return True


        def interrupt_confirm(self):
            """
            Checks to see if there's a game in progress as defined
            by the self.gameInProgress variable in the Application.
            If there is, display a popup window asking the user to confirm whether
            they want to interrupt the game in progress.
            """
            log_status("Start of interrupt_confirm.")
            # Check to see if there's a game in progress.
            # If there is, prompt the user to confirm they want to stop the game.
            if self.gameInProgress:
                self.confirmPopup = self.popup("Do you really want to stop this game?", button1Text="Yes", button2Text="No")
                interrupt = self.interrupt_value()

                if not interrupt:
                    log_status("    Returning False")
                    return False
                else:
                    log_status("    Returning True")
                    return True

            log_status("    Returning True")
            return True


        def reset(self):
            """
            Resets various variables used by the Application to original values,
            as if the program had just been opened, such that nothing will interfere
            with a different operation than was previously in progress.
            """
            log_status("Start of reset.")
            # Reset everything. All variables, buttons, menu items, etc.
            canvas.delete("all")
            
            if self.historyImages:
                for i in self.historyImages:
                    i.place_forget()
                    
            self.startText = canvas.create_text(10, 10, text=startText, font=("calibri", 16), anchor=tk.NW)
            self.bingoFullPath = None
            self.bingoType = None
            self.bingoCards = []
            self.wordsFile = None
            self.pictures = []
            self.historyPictures = []
            self.displayPictures = []
            self.words = []
            self.calledItems = []
            self.xOffset = 0
            self.yOffset = 0
            self.gameInProgress = False
            self.historyImages = []

            self.nextImage["state"] = tk.DISABLED

            fileMenu.entryconfig("Display next image/word", state=tk.DISABLED)
            fileMenu.entryconfig("Open bingo cards folder", state=tk.DISABLED)
            
            self.dBindId = self.enable_binding("d", self.ctrl_d)
            self.cBindId = self.enable_binding("c", self.ctrl_c)

            self.disable_binding("d", self.dBindId)
            self.disable_binding("c", self.cBindId)


        def check_number_of_items(self):
            """
            Prompts the user to select either a folder (for Picture Bingo)
            or a file (for Word Bingo) and checks the selection for an
            appropriate number of items.

            If an inappropriate number of items is detected, prompt the user
            to add or remove items if there are too few or too many, respectively.
            
            Returns a String of the path to the folder/file.
            """
            log_status("Start of check_number_of_items.")
            if self.bingoType == "pictures":
                # Prompt the user for a folder of images to use.
                while True:
                    folder = filedialog.askdirectory(title="Select the folders the pictures are in.")
                    if not folder:
                        log_status("    Returning False")
                        return None

                    # Set the pictures to the list of files in the folder.
                    self.pictures = [file for file in os.listdir(folder) if os.path.isfile(os.path.join(folder, file))]

                    # Each square has to have a different picture, so check to see if there are enough.
                    if len(self.pictures) < 25:
                        self.popup("Your folder needs to have at least 25 pictures in it!", button1Text="Ok")
                        continue
                    # Unless I make a fancier way of dealing with history, the screen space dictates how many files you can have.
                    # Bingo is traditionally 75 possibilities, so this should be plenty.
                    elif len(self.pictures) > 95:
                        self.popup("Sorry, this program can only handle up to 95 pictures.\r\nPlease remove some images from the folder and try again.", button1Text="Ok")
                        continue
                    
                    break

                log_status("    Returning " + folder)
                return folder
            elif self.bingoType == "words":
                while True:
                    # Prompt the user for a file that contains the words to use.
                    file = filedialog.askopenfilename(title="Select the file the words are in.", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
                    if not file:
                        log_status("    Returning False")
                        return None

                    f = open(file, "r").readlines()

                    # Only take unique words. No blanks.
                    self.words = list(set([word.replace("\r", "").replace("\n", "") for word in f if word.strip()]))

                    # Each square has to have a different word, so check to see if there are enough.
                    if len(self.words) < 25:
                        self.popup("Your words file must have at least 25 unique words in it (one word per line)!", button1Text="Ok")
                        continue
                    # Unless I make a fancier way of dealing with history, the screen space dictates how many words you can have.
                    # Bingo is traditionally 75 possibilities, so this should be plenty.
                    elif len(self.words) > 105:
                        self.popup("Sorry, this program can only handle up to 105 words.\r\nPlease remove some words from the file and try again.", button1Text="Ok")
                        continue
                    
                    break

                log_status("    Returning " + file)
                return file


        def get_number_of_cards(self):
            """
            Prompts the user to enter the number of Bingo cards they wish to create.
            Returns an Integer of the number of cards.
            """
            log_status("Start of get_number_of_cards.")
            # Prompt the user to enter the number of cards they want to create.
            # Must be a positive whole number.
            while True:
                self.cardsPopup = self.popup("Enter the number of Bingo cards to generate.", entry=True, button1Text="Ok")
                
                try:
                    cards = int(self.cards_value())
                except ValueError:
                    self.popup("It has to be a positive whole number!", button1Text="Ok")
                    continue
                except:
                    raise

                if cards <= 0:
                    self.popup("You need at least one card!", button1Text="Ok")
                    continue

                break

            log_status("    Returning " + str(cards))
            return cards


        def create_bingo_cards(self, freeSpace, cards):
            """
            Creates the individual Bingo cards.

            Requird Parameters:
                freeSpace: Boolean
                    Whether to have the central square in each card be a "free space".

                cards: Integer
                    The number of Bingo cards to create.
            """
            log_status("Start of create_bingo_cards: freeSpace=" + str(freeSpace) + ", cards=" + str(cards))
            columns = 5
            rows = 5
            
            # Since I don't know how long this could take, display a progress bar.
            self.progressLabel = tk.Label(root, text="Creating bingo cards...")
            self.progressLabel.place(x=450, y=530)
            self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode="determinate")
            self.progress.place(x=450,y=550)

            for c in range(cards):
                self.progress["value"] = (c + 1) / cards
                root.update_idletasks()
                # Create a card.
                self.generate_html_card(c, columns, rows, freeSpace)

            # Ditch the progress bar.
            self.progress.place_forget()
            self.progressLabel.place_forget()


        def delete_create_folder(self, folderName):
            """
            Looks for a folder.  If it exists, delete it.  Then if it doesn't exist, create it.
            
            Required Parameters:
                folderName: String
                    The folder path to delete/create.
            """
            log_status("Start of delete_create_folder: folderName=" + str(folderName))

            # If it already exists, delete it.
            if os.path.exists(folderName) and not os.path.isfile(folderName):
                log_status("Deleting " + str(folderName))
                shutil.rmtree(folderName)

            # If it doesn't exist, create it.
            if not os.path.exists(folderName) and not os.path.isfile(folderName):
                log_status("Creating " + str(folderName))
                os.makedirs(folderName)

        def generate_bingo_cards(self, bingoType=None):
            """
            Creates a new set of bingo cards.

            Optional Parameters:
                bingoType: String
                    The type of bingo cards to create (words or pictures).
                    Default: None
            """
            log_status("Start of generate_bingo_cards: bingoType=" + str(bingoType))
            # Check to see if we're interrupting a game by doing this.
            if not self.interrupt_confirm():
                return

            # Reset everything.
            self.reset()

            # Save a .bingo file to store the locations of important files in the working_dir folder.
            dest = self.save_bingo_file()

            # If we chose not to save, reset everything and return.
            if not dest:
                self.reset()
                return

            # If we got here via a generic "New" command, prompt the user for which type of Bingo.
            if not bingoType:
                self.bingoTypePopup = self.popup("Which type of Bingo cards do you want to create?", button1Text="Words", button2Text="Pictures")
                if self.bingo_type_value():
                    bingoType = "words"
                else:
                    bingoType = "pictures"

            self.bingoType = bingoType

            # Prompt the user to select a file for word Bingo or a folder for picture Bingo.
            # For words, check the number of lines in the file.
            # For pictures, check the number of files in the folder.
            items = self.check_number_of_items()

            # If we didn't select a file/folder, reset and return.
            if not items:
                self.reset()
                return

            # Create a folder named after the .bingo file under the working_dir folder.
            # This is where the relevant files for this Bingo game will live.
            workingDirName = os.path.splitext(os.path.basename(dest))[0]
            self.bingoFullPath = os.path.dirname(__file__) + "\\working_dir\\" + workingDirName
            self.delete_create_folder(self.bingoFullPath)

            # Create subfolders to house the different sizes of pictures.
            if bingoType == "pictures":
                self.delete_create_folder(self.bingoFullPath + "\\card_pictures")
                self.delete_create_folder(self.bingoFullPath + "\\display_pictures")
                self.delete_create_folder(self.bingoFullPath + "\\history_pictures")
                self.delete_create_folder(self.bingoFullPath + "\\bingo_cards")

            # If we're generating cards, there is no game in progress and
            # we should not be able to ask for the next image/word.
            self.gameInProgress = False
            self.nextImage["state"] = tk.DISABLED

            # Prompt the user for the number of Bingo cards they want to create.
            cards = self.get_number_of_cards()

            # Prompt the user for whether they want a "FREE SPACE" in the middle square in each card.
            self.freeSpacePopup = self.popup("Do want a free space in the middle square?", button1Text="Yes", button2Text="No")
            freeSpace = self.free_space_value()

            if self.bingoType == "pictures":
                # Since I don't know how long this could take, display a progress bar.
                self.progressLabel = tk.Label(root, text="Processing images...")
                self.progressLabel.place(x=450, y=530)
                self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode="determinate")
                self.progress.place(x=450,y=550)
                
                # Create the necessary files for picture Bingo:
                for i, picture in enumerate(self.pictures):
                    self.progress["value"] = i / len(self.pictures)
                    root.update_idletasks()
                    
                    # Medium images to be in the bingo cards.
                    newCardPicture = self.resize_image(items, self.bingoFullPath, picture, i, "card", 150)
                    if not newCardPicture:
                        self.reset()
                        log_status("    Returning after reset.")
                        return
                    
                    self.cardPictures.append(newCardPicture)
                    
                    # Small images to be in the history during play.
                    newHistoryPicture = self.resize_image(items, self.bingoFullPath, picture, i, "history", 50)
                    if not newHistoryPicture:
                        self.reset()
                        log_status("    Returning after reset.")
                        return
                    
                    self.historyPictures.append(newHistoryPicture)
                    
                    # Large images for display when you click the "Display next image/word" button.
                    newDisplayPicture = self.resize_image(items, self.bingoFullPath, picture, i, "display", 350)
                    if not newDisplayPicture:
                        self.reset()
                        log_status("    Returning after reset.")
                        return
                    
                    self.displayPictures.append(newDisplayPicture)

                # Ditch the progress bar.
                self.progress.place_forget()
                self.progressLabel.place_forget()

            self.create_bingo_cards(freeSpace, cards)

            # Save the dict again.
            self.save_dict_file(dest)

            # Everything should be set to go!
            self.prep_for_play()
            

        def prep_for_play(self):
            """
            Randomizes the lists of display items for playing Bingo.
            Enables the button/menu item to view the bingo cards
            and display the next image or word.
            """
            log_status("Start of prep_for_play.")
            # Randomize the lists that will be displayed when you click the "Display next image/word" button.
            random.shuffle(self.displayPictures)
            random.shuffle(self.words)

            # Enable the buttons/menus to view the bingo cards as well as display the next image or word.
            self.nextImage["state"] = tk.NORMAL

            fileMenu.entryconfig("Display next image/word", state=tk.NORMAL)
            fileMenu.entryconfig("Open bingo cards folder", state=tk.NORMAL)
            
            self.dBindId = self.enable_binding("d", self.ctrl_d)
            self.cBindId = self.enable_binding("c", self.ctrl_c)


        def play_bingo(self):
            """
            Loads a .bingo card fore viewing and/or playing.
            """
            log_status("Start of play_bingo.")
            # Check to see if there's already a game in progress.
            if not self.interrupt_confirm():
                return

            self.reset()

            # Get a .bingo file to play.
            if not self.load_file():
                return

            # Set everything up!
            self.prep_for_play()


        def display_next_image_or_word(self):
            """
            Displays the next item in the randomized list of items while playing Bingo.
            """
            log_status("Start of display_next_image_or_word.")
            self.gameInProgress = True

            # Remove the instructions if they're on screen.
            if self.startText:
                canvas.delete(self.startText)

            if self.bingoType == "pictures":
                items = self.displayPictures
                
                # Get the next image.
                calledItem = self.displayPictures.pop(0)
                self.calledItems.append(calledItem)
                img = ImageTk.PhotoImage(Image.open(calledItem))

                # If an image has already been displayed, delete it so we're not just piling images on top of one another.
                if len(self.calledItems) > 1:
                    canvas.delete(self.displayCanvas)

                # Display the image.
                self.displayCanvas = canvas.create_image(500, 625, anchor=tk.S, image=img)
                canvas.image = img

                # Put the called images into the history.
                hImg = ImageTk.PhotoImage(Image.open(calledItem.replace("/display_pictures/", "/history_pictures/").replace("_display.", "_history.")))
                hi = tk.Label(image=hImg)
                hi.image = hImg

                # Place this image at x,y coordinates on screen, starting near the top left,
                # going across the screen to the right, then starting a new row.
                hi.place(x=5 + self.xOffset, y=10 + self.yOffset)
                self.historyImages.append(hi)
                self.xOffset += 52

                if len(self.calledItems) % 19 == 0:
                    self.yOffset += 50
                    self.xOffset = 0
            elif self.bingoType == "words":
                items = self.words
                
                # Display the next word.
                self.calledItems.append(self.words.pop(0))
                if len(self.calledItems) > 1:
                    canvas.delete(self.displayCanvas)
                self.displayCanvas = canvas.create_text(500, 500, text=self.calledItems[-1], font=("calibri", 40), anchor=tk.S)

                # Put the called word into the history.
                for hc in self.historyCanvas:
                    canvas.delete(hc)

                self.historyCanvas = []

                # Words are displayed down the left side of the screen,
                # then creating another column.
                for x in range(ceil(len(self.calledItems) / 15)):
                    xCoord = (10 if x == 0 else x * 150)
                    # Set the index range.
                    iFrom = x * 15
                    iTo = min([(x + 1) * 15, len(self.calledItems)])
                    self.historyCanvas.append(canvas.create_text(xCoord, 10, text="\n".join(self.calledItems[iFrom: iTo]), font=("calibri", 14), anchor=tk.NW))

            # If all items have been displayed, show a popup informing the user.
            # Disable the display button/menu.
            # Set the game as finished so you don't have to confirm if you generate/load from here.
            if len(items) == 0:
                self.disable_binding("d", self.dBindId)
                self.nextImage["state"] = tk.DISABLED
                fileMenu.entryconfig("Display next image/word", state=tk.DISABLED)
                self.popup("That's all the " + self.bingoType + ". Someone better have a Bingo by now!", button1Text="Ok")
                self.gameInProgress = False
                return
                    

        def create_buttons(self):
            """
            Create the button for displaying the next item while playing Bingo.
            """
            log_status("Start of create_buttons.")
            self.nextImage = tk.Button(self)
            self.nextImage["text"] = "Display the next image/word"
            self.nextImage["font"] = ("calibri", 16)
            self.nextImage["command"] = self.display_next_image_or_word
            self.nextImage.pack({"side": "left"})
            self.nextImage["state"] = tk.DISABLED
            self.buttons.append(self.nextImage)


        def popup(self, labelText, entry=False, button1Text=None, button2Text=None):
            """
            Create a popup window for informing or requesting information from the user.

            Required Parameters:
                labelText: String
                    The text displayed in the popup window.

            Optional Parameters:
                entry: Boolean
                    Whether to display a free text entry box.
                    Default: False

                button1Text: String
                    The text to display in the first button. If None, no button is displayed.
                    Default: None

                button2Text: String
                    The text to display in the second button. If None, no button is displayed.
                    Default: None
            """
            log_status("Start of popup: labelText=" + labelText + ", entry=" + str(entry) + ", button1Text=" + str(button1Text) + ", button2Text=" + str(button2Text))
            p = popupWindow(self.master, labelText, entry=entry, button1Text=button1Text, button2Text=button2Text)
            
            for b in self.buttons:
                b["state"] = tk.DISABLED

            menuBar.entryconfig("File", state=tk.DISABLED)
                
            self.master.wait_window(p.top)
            for b in self.buttons:
                b["state"] = tk.NORMAL

            menuBar.entryconfig("File", state="normal")

            log_status("    Returning")
            return p
            

        def free_space_value(self):
            """
            Returns the value that was selected about whether the user
            wants a "free space" in the bingo cards.
            """
            log_status("free_space_value returning " + str(self.freeSpacePopup.value))
            return self.freeSpacePopup.value
            

        def bingo_type_value(self):
            """
            Returns the value that was selected about whether the user
            wants to create word or picture bingo cards.
            """
            log_status("free_space_value returning " + str(self.bingoTypePopup.value))
            return self.bingoTypePopup.value
            

        def cards_value(self):
            """
            Returns the value that was for the number of bingo cards to create.
            """
            log_status("free_space_value returning " + str(self.cardsPopup.value))
            return self.cardsPopup.value


        def interrupt_value(self):
            """
            Returns the value that was selected about whether the user
            wants a to interrupt the current game of bingo.
            """
            log_status("free_space_value returning " + str(self.confirmPopup.value))
            return self.confirmPopup.value


        def ctrl_w(self, event):
            """
            Keyboard shortcut for creating a new set of word bingo cards.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.generate_bingo_cards("words")


        def ctrl_p(self, event):
            """
            Keyboard shortcut for creating a new set of picture bingo cards.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.generate_bingo_cards("pictures")


        def ctrl_o(self, event):
            """
            Keyboard shortcut for opening a .bingo file for viewing and/or playing.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.play_bingo()


        def ctrl_q(self, event):
            """
            Keyboard shortcut for exiting the program.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            root.quit()


        def ctrl_n(self, event):
            """
            Keyboard shortcut for creating a new set of bingo cards. The type is to be determined.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.generate_bingo_cards()


        def ctrl_d(self, event):
            """
            Keyboard shortcut for displaying the next item while playing bingo.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.display_next_image_or_word()


        def ctrl_c(self, event):
            """
            Keyboard shortcut for displaying the next item while playing bingo.

            Required Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            self.open_bingo_cards_folder()


        def disable_binding(self, bindKey, bindId):
            """
            Disables a keyboard shortcut.

            Required Parameters:
                bindKey: String
                    The key combination to be disabled.

                bindId: String
                    The ID from when the shortcut was enabled.
            """
            log_status("Start of disable_binding: bindKey=" + bindKey + ", bindId=" + bindId)
            self.unbind("<" + bindKey + ">", bindId)


        def enable_binding(self, bindKey, method):
            """
            Creates a keyboard shortcut.

            Required Parameters:
                bindKey: String
                    The key combination to be bound to a method.

                method: method/function
                    The method or function to run when the key combination is pressed.
            """
            log_status("Start of enable_binding: bindKey=" + bindKey + ", method=" + str(method))
            return self.bind_all("<Control-" + bindKey + ">", method)
        

    class popupWindow(object):
        """
        A popup window that either displays a message for the user or asks
        for input in the form of an entry field or a choice of two options.

        Required parameters:
            master: tkinter.Tk object
                The tkinter Tk object (root).
                
            labelText: String
                The message to be displayed in the popup window.

        Optional parameters:
            entry: Boolean
                Whether a free text entry box is in the popup window.
                Default: False

            button1Text: String
                The text displayed on the first button.
                Default: None

            button2Text: String
                The text displayed on the second button.
                Default: None
        """
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
                    self.b1 = tk.Button(top, text=button1Text, font=("calibri", 16), command=self.cleanupTrue)

                self.b1.pack()

            if button2Text:
                self.b2 = tk.Button(top, text=button2Text, font=("calibri", 16), command=self.cleanupFalse)
                self.b2.pack()
            
            
        def cleanupTrue(self):
            """
            Sets the "value" of the popup window object to True and removes the popup window.
            """
            log_status("    Cleaning up popup with value of True")
            self.value = True
            self.top.destroy()
            
            
        def cleanupFalse(self):
            """
            Sets the "value" of the popup window object to False and removes the popup window.
            """
            log_status("    Cleaning up popup with value of False")
            self.value = False
            self.top.destroy()

            
        def cleanupEntry(self):
            """
            Sets the "value" of the popup window object to what the user entered in the entry box
            and removes the popup window.
            """
            log_status("    Cleaning up popup with value of " + str(self.e.get()))
            self.value = self.e.get()
            self.top.destroy()


    log_status("Start", writeType="w")

    fileFolderDict = {}

    # If the working_dir folder doesn't exist, create it.
    if not os.path.exists(os.path.dirname(__file__) + "//working_dir"):
        log_status("Creating working_dir folder.")
        os.makedirs(os.path.dirname(__file__) + "//working_dir")

    # If the fileFolderDict.p file doesn't exist, create it with an empty dictionary.
    if not os.path.exists(os.path.dirname(__file__) + "//fileFolderDict.p"):
        log_status("Creating default fileFolderDict.p.")
        pickle.dump(fileFolderDict, open(os.path.dirname(__file__) + "//fileFolderDict.p", "wb"), -1)

    # Load the data in fileFolderDict.p.
    if os.path.getsize("fileFolderDict.p") > 0:
        log_status("Loading fileFolderDict.p.")
        with open("fileFolderDict.p", "rb") as f:
            unpickler = pickle.Unpickler(f)
            fileFolderDict = unpickler.load()

    startText = """Bingo creator/player

    To create Bingo cards:
    1. Setup
        a. Word Bingo - create a file with a word on each line (25-105 words).
        b. Picture Bingo - Put your Bingo images into a folder with nothing else in it (25-95 images).
    2. Click File --> New Bingo Cards --> select which kind of Bingo cards you want.
       Alternatively, click File --> New Word Bingo Cards or New Picture Bingo Cards.
       Save a .bingo file.
    3. Choose whether you want a "free space" in the center square.
    4. Choose the things to display in the cards.
        a. Word Bingo - Select the file that contains the Bingo words.
        b. Picture Bingo - Select the folder with your Bingo images in it.
    3. Follow remaining instructions.

    To play Bingo:
    1. Click File --> Load Bingo button.
    2. Open a .bingo file you created in create step 2 above.
    3. Click the \"Display next image/word\" button until someone wins!"""

    # Header for the HTML file used for the Bingo cards.
    head = ("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\" \"http://www.w3.org/TR/html4/strict.dtd\">\n"
            "<html lang=\"en\">\n<head>\n"
            "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
            "<title>Bingo Cards</title>\n"
            "<style type=\"text/css\">\n"
            "\tbody { font-size: 30px; }\n"
            "\ttable { margin: 20px auto; border-spacing: 2px; }\n"
            "\t.newpage { page-break-after:always; }\n"
            "\ttr { height: 80px; }\n"
            "\ttd { text-align: center; border: thin black solid; padding: 10px; width: 80px; }\n"
            "</style>\n</head>\n<body>\n")

    tail = "</body></html>"

    path_wkthmltoimage = os.path.dirname(__file__) + "\\" + r'wkhtmltopdf\bin\wkhtmltoimage.exe'
    config = imgkit.config(wkhtmltoimage=path_wkthmltoimage)

    root = tk.Tk()
    canvas = tk.Canvas(root, width = 1000, height = 615)
    canvas.pack()
    root.resizable(False, False)
    app = Application(master=root)
    menuBar = tk.Menu(root)
    fileMenu = tk.Menu(menuBar, tearoff=0)
    fileMenu.add_command(label="New Bingo Cards", command=lambda: app.generate_bingo_cards(), accelerator="Ctrl+N")
    fileMenu.add_command(label="New Word Bingo Cards", command=lambda: app.generate_bingo_cards("words"), accelerator="Ctrl+W")
    fileMenu.add_command(label="New Picture Bingo Cards", command=lambda:app.generate_bingo_cards("pictures"), accelerator="Ctrl+P")
    fileMenu.add_command(label="Load Bingo File", command=app.play_bingo, accelerator="Ctrl+O")
    fileMenu.add_command(label="Display next image/word", command=lambda: app.display_next_image_or_word(), state=tk.DISABLED, accelerator="Ctrl+D")
    fileMenu.add_command(label="Open bingo cards folder", command=lambda: app.open_bingo_cards_folder(), state=tk.DISABLED, accelerator="Ctrl+C")
    fileMenu.add_separator()
    fileMenu.add_command(label="Quit", command=root.quit, accelerator="Ctrl+Q")
    menuBar.add_cascade(label="File", menu=fileMenu)

    root.config(menu=menuBar)
    app.mainloop()
    log_status("Closing application.")
    root.destroy()
except:
    error =str(sys.exc_info())
    if "application has been destroyed" not in error:
        log_status("Logging error.")
        errorFile = open("errors.txt", "a")
        errorFile.write(str(datetime.datetime.now()) + ": " + error + "\n")
        errorFile.close()
        raise
