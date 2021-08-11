try:
    import random
    import sys
    import os
    import base64
    import imgkit
    import logging
    import inspect
    import fpdf
    import re
    import pickle
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk
    from PIL import Image, ImageTk
    import PIL
    from math import ceil, floor


    class CustomAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            my_context = kwargs.pop("caller", self.extra["caller"])
            return "[%s] %s" % (my_context, msg), kwargs


    class CustomException(Exception):
        pass


    def enable_binding(bindKey, method):
        """
        Sets a keyboard shortcut.

        Required Parameters:
            bindKey: String
                The key combination to be bound to a method.

            method: method/function
                The method or function to run when the key combination is pressed.
        """
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            adapter.debug("Start of enable_binding: bindKey=" + bindKey + ", method=" + str(method), caller=calframe[1][3])
            adapter.debug("End of enable_binding")
            return root.bind_all("<" + bindKey + ">", method)
        except Exception as e:
            adapter.exception(e)
            raise


    def do_nothing(event=None):
        """
        This is what disabled keyboard shortcuts are set to.
        I made this because apparently you can't set them to None
        after they've been set to something else.
        And I was having issues with disabling bindings as well.
        """
        pass


    logger = logging.getLogger(__name__)
    formatter = logging.Formatter("%(asctime)s|%(levelname)s|%(message)s", "%d/%m/%Y %H:%M:%S")
    fh = logging.FileHandler(os.path.dirname(os.path.realpath(__file__)) + "\log.txt", "w")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    adapter = CustomAdapter(logger, {"caller": ""})
    logger.setLevel(logging.DEBUG)


    class Application(tk.Frame):
        def __init__(self, master=None):
            try:
                adapter.debug("Initiating application")
                tk.Frame.__init__(self, master)
                self.pack()
                self.buttons = set()
                self.create_buttons()
                self.bingoFile = None
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
                self.displayedHistoryPictures = []
                self.historyCanvas = []

                # Create the keyboard shortcuts.
                self.wBindId = enable_binding("Control-w", lambda x: self.keybind_call("w"))
                self.pBindId = enable_binding("Control-p", lambda x: self.keybind_call("p"))
                self.qBindId = enable_binding("Control-q", lambda x: self.keybind_call("q"))
                self.oBindId = enable_binding("Control-o", lambda x: self.keybind_call("o"))
                # These do nothing for now because they are only valid when a .bingo file has been loaded.
                self.rightBindId = enable_binding("Right", do_nothing)
                self.leftBindId = enable_binding("Left", do_nothing)
                self.gBindId = enable_binding("Control-n", do_nothing)
                self.sBindId = enable_binding("Control-s", do_nothing)
                self.cBindId = enable_binding("Control-c", do_nothing)

                # Find all the .bingo files and associated folders that are stored in the dict
                # and delete one if the other doesn't exist.
                keysToDelete = []
                for k, v in fileFolderDict.items():
                    if not os.path.exists(k) or not os.path.exists(v):
                        if os.path.exists(k) and os.path.splitext(k) == ".bingo":
                            adapter.warning("Deleting " + k)
                            os.remove(k)
                        self.delete_unused_files_folders(v)

                        keysToDelete.append(k)

                for k in keysToDelete:
                    adapter.warning("Deleting key " + k + " from fileFolderDict.")
                    del fileFolderDict[k]

                # Save the dictionary in case there were any changes.
                adapter.debug("Saving fileFolderDict.p")
                with open("fileFolderDict.p", "wb") as f:
                    pickler = pickle.Pickler(f)
                    pickler.dump(fileFolderDict)

                adapter.debug("Application initiated")
            except Exception as e:
                adapter.exception(e)
                raise


        def delete_unused_files_folders(self, rootDir):
            if os.path.exists(rootDir):
                for root, dirs, files in os.walk(rootDir):
                    for file in files:
                        if re.match("bingo_generator_[0-9]+\.", file):
                            adapter.warning("Deleting " + os.path.abspath(os.path.join(root, file)))
                            os.remove(os.path.abspath(os.path.join(root, file)))

                for root, dirs, files in os.walk(rootDir):
                    for dir in dirs:
                        if not os.listdir(os.path.join(root, dir)):
                            adapter.warning("Deleting " + os.path.join(root, dir))
                            os.rmdir(os.path.join(root, dir))

                if not os.listdir(rootDir):
                    adapter.warning("Deleting " + rootDir)
                    os.rmdir(rootDir)
            

        def generate_html_card(self, cardNum, freeSpace):
            """
            Generates an HTML file of the bingo card.
            Then converts the HTML file into an image.

            Required Parameters:
                cardNum: Integer
                    The number of this card, used to generate distinct file names.

                freeSpace: Boolean
                    Whether there is a "free space" in the center square of the table.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of generate_html_card: cardNum=" + str(cardNum) + ", freeSpace=" + str(freeSpace), caller=calframe[1][3])
                
                # Get a random sample of the words/pictures with which to fill in this card.
                if self.bingoType == "pictures":
                    ps = random.sample(self.cardPictures, 25)
                elif self.bingoType == "words":
                    ps = random.sample(self.words, 25)
                    
                res = "<table>\n"
                    
                for i, item in enumerate(ps):
                    if i % 5 == 0:
                        res += "\t<tr>\n"
                        
                    if i == 12 and freeSpace:
                        res += "\r<td>FREE SPACE</td>\n"
                    elif self.bingoType == "pictures":
                        # Embed the picture in the HTML file so it can be opened without the picture files existing.
                        res += "\t\t<td><img src=\"data:image/png;base64,{0}\"></td>\n".format(base64.b64encode(open(item, "rb").read()).decode("utf-8"))
                    elif self.bingoType == "words":
                        res += "\t\t<td>" + item + "</td>\n"
                        
                    if i % 5 == 4:
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
                imgkit.from_file(self.bingoFullPath + "\\" + "bingo_card.html", self.bingoFullPath + "\\bingo_cards\\bingo_generator_" + str(cardNum) + ".jpg", config=config)

                # Delete the HTML file.
                os.remove(self.bingoFullPath + "\\" + "bingo_card.html")

                # Add the location of the image to what will be saved in the .bingo file.
                self.bingoCards.append(self.bingoFullPath + "\\bingo_cards\\bingo_generator_" + str(cardNum) + ".jpg")

                adapter.debug("End of generate_html_card", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise

        def save_bingo_cards(self):
            """
            Combines the bingo card images into a single PDF for ease of printing.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of save_bingo_cards", caller=calframe[1][3])

                # Prompt the user to save the .pdf file.
                output = filedialog.asksaveasfile(mode="w", initialdir=os.getcwd(), defaultextension=".pdf")

                if not output:
                    adapter.debug("End of save_bingo_file (nothing done)")
                    return

                pdf = fpdf.FPDF()
                for card in self.bingoCards:
                    pdf.add_page(orientation="Landscape")
                    pdf.image(card, w=193)
                pdf.output(output.name, "F")

                adapter.debug("End of save_bingo_cards", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


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
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of resize_image: folder=" + folder + ", destFolder=" + destFolder + ", picture=" + picture + ", pictureNum=" + str(pictureNum) + ", maxSideSize=" + str(maxSideSize), caller=calframe[1][3])

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
                resizedFileName = destFolder + "/" + pictureType + "_pictures/bingo_generator_" + str(pictureNum) + os.path.splitext(folder + "/" + picture)[1]
                img.save(resizedFileName)
                
                adapter.debug("    Returning " + resizedFileName)
                adapter.debug("End of resize_image")
                return resizedFileName
            except PIL.UnidentifiedImageError:
                self.popup(picture + " is not a recognized image format!\r\nPlease make sure your Bingo images folder has ONLY images in it!", button1Text="Ok")
                adapter.debug("    Returning None")
                adapter.debug("End of resize_image")
                return None
            except Exception as e:
                adapter.exception(e)
                raise


        def save_bingo_file(self):
            """
            Saves a .bingo file so this game can be loaded later.
            Returns a String containing the file name.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of save_bingo_file", caller=calframe[1][3])
                
                self.bingoTypePopup = self.popup("First save a file that will contain the information for this bingo game.", button1Text="Ok")
                
                # Prompt the user to save the .bingo file.
                output = filedialog.asksaveasfile(mode="w", initialdir=os.getcwd(), defaultextension=".bingo")

                if not output:
                    adapter.debug("End of save_bingo_file (nothing done)")
                    return

                # Update the dict that tracks all file locations for this bingo game.
                fileFolderDict[output.name] = os.path.dirname(__file__) + "//working_dir//" + os.path.splitext(os.path.basename(output.name))[0]
                with open("fileFolderDict.p", "wb") as f:
                    pickler = pickle.Pickler(f)
                    pickler.dump(fileFolderDict)

                # Update the dict that tracks all file locations for this bingo game.
                self.save_dict_file(output.name)

                adapter.debug("    Returning " + output.name)
                adapter.debug("End of save_bingo_file")
                return output.name
            except Exception as e:
                adapter.exception(e)
                raise


        def save_dict_file(self, bingoName):
            """
            Saves data on file locations to a .bingo file.

            Required Parameters:
                bingoName: String
                    The file name of the .bingo file.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of save_dict_file: bingoName=" + bingoName, caller=calframe[1][3])

                # Save the dict for this Bingo game that tracks locations of files.
                pickler = open(bingoName, "wb")

                pickleDict = {
                    "bingoCards": self.bingoCards,
                    "words": self.words,
                    "historyPictures": self.historyPictures,
                    "displayPictures": self.displayPictures,
                    "cardPictures": self.cardPictures,
                    "workLocation": self.bingoFullPath
                    }

                pickle.dump(pickleDict, pickler, -1)

                pickler.close()

                adapter.debug("End of save_dict_file", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def load_bingo_file(self):
            """
            Loads a .bingo file and sets the following variables in the Application:
                self.bingoCards
                self.words
                self.historyPictures
                self.displayPictures
                self.bingoType
                self.bingoFullPath
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of load_bingo_file", caller=calframe[1][3])

                # Prompt the user for a .bingo file to load.
                loadFile = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Bingo file to open", filetypes = [("Bingo files", ".bingo")])
                if not loadFile:
                    return False
                
                if os.path.splitext(loadFile)[1] != ".bingo":
                    self.popup("Invalid file type.\r\nPlease select a valid .bingo file!", button1Text="Ok")
                    return False

                pickler = open(loadFile, "rb")
                pickleDict = pickle.load(pickler)
                pickler.close()

                # Set variables from the pickled dict.
                self.bingoCards = pickleDict["bingoCards"]
                self.words = pickleDict["words"]
                self.historyPictures = pickleDict["historyPictures"]
                self.displayPictures = pickleDict["displayPictures"]
                self.cardPictures = pickleDict["cardPictures"]
                self.bingoFullPath = pickleDict["workLocation"]

                if self.words:
                    self.bingoType = "words"
                elif self.displayPictures:
                    self.bingoType = "pictures"
                else:
                    # Something's wrong with this .bingo file (like someone started to make one then exited)
                    self.popup("Something is wrong with that .bingo file.\r\nPlease choose a different one or create a new one.", button1Text="Ok")
                    raise CustomException("Bad .bingo file, resetting.")

                adapter.debug("    Returning True")
                adapter.debug("End of load_bingo_file")
                return loadFile
            except Exception as e:
                adapter.exception(e)
                raise


        def interrupt_confirm(self):
            """
            Checks to see if there's a game in progress as defined
            by the self.gameInProgress variable in the Application.
            If there is, display a popup window asking the user to confirm whether
            they want to interrupt the game in progress.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of interrupt_confirm", caller=calframe[1][3])

                # Check to see if there's a game in progress.
                # If there is, prompt the user to confirm they want to stop the game.
                if self.gameInProgress:
                    self.interruptPopup = self.popup("Do you really want to stop this game?", button1Text="Yes", button2Text="No")

                    if not self.interruptPopup.value:
                        adapter.debug("End of interrupt_confirm")
                        adapter.debug("    Returning False")
                        return False
                    else:
                        adapter.debug("End of interrupt_confirm")
                        adapter.debug("    Returning True")
                        return True

                adapter.debug("    Returning True")
                adapter.debug("End of interrupt_confirm")
                return True
            except Exception as e:
                adapter.exception(e)
                raise


        def more_cards_confirm(self):
            """
            Checks to see if there's a game in progress as defined
            by the self.gameInProgress variable in the Application.
            If there is, display a popup window asking the user to confirm whether
            they want to interrupt the game in progress.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of more_cards_confirm", caller=calframe[1][3])

                # It would take a lot to be able to make new cards that are guaranteed to not match the ones
                # we already made, even those chances are low, so let's just delete the existing ones.
                self.moreCardsPopup = self.popup("This will delete existing cards and create new ones, are you sure?", button1Text="Yes", button2Text="No")

                if not self.moreCardsPopup.value:
                    adapter.debug("End of more_cards_confirm")
                    adapter.debug("    Returning False")
                    return False
                else:
                    adapter.debug("End of more_cards_confirm")
                    adapter.debug("    Returning True")
                    return True
            except Exception as e:
                adapter.exception(e)
                raise


        def new_game(self):
            """
            Partial reset to play another game of Bingo with newly randomized items.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of new_game", caller=calframe[1][3])
                
                if self.gameInProgress and not self.interrupt_confirm():
                    adapter.debug("End of new_game (nothing done)")
                    return

                canvas.delete("all")
                
                if self.displayedHistoryPictures:
                    for i in self.displayedHistoryPictures:
                        i.place_forget()

                if self.bingoType == "pictures":
                    self.displayPictures += self.calledItems
                    self.displayedHistoryPictures = []
                else:
                    self.words += self.calledItems

                self.calledItems = []
                self.xOffset = 0
                self.yOffset = 0

                self.prep_for_play()
                
                self.display_next_item()

                adapter.debug("End of new_game", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def reset(self):
            """
            Resets various variables used by the Application to original values,
            as if the program had just been opened, such that nothing will interfere
            with a different operation than was previously in progress.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of reset", caller=calframe[1][3])

                # Reset everything. All variables, buttons, menu items, etc.
                canvas.delete("all")
                
                if self.displayedHistoryPictures:
                    for i in self.displayedHistoryPictures:
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
                self.displayedHistoryPictures = []

                gameMenu.entryconfig("Display next item", state=tk.DISABLED)
                gameMenu.entryconfig("Display previous item", state=tk.DISABLED)
                gameMenu.entryconfig("Save bingo cards to PDF", state=tk.DISABLED)
                gameMenu.entryconfig("New Game", state=tk.DISABLED)
                gameMenu.entryconfig("New bingo cards", state=tk.DISABLED)

                self.nextItem["state"] = tk.DISABLED
                self.previousItem["state"] = tk.DISABLED
                self.newGame["state"] = tk.DISABLED
                self.saveBingoCards["state"] = tk.DISABLED
                
                self.rightBindId = enable_binding("Right", do_nothing)
                self.sBindId = enable_binding("Control-s", do_nothing)
                self.leftBindId = enable_binding("Left", do_nothing)
                self.nBindId = enable_binding("Control-n", do_nothing)
                self.cBindId = enable_binding("Control-c", do_nothing)

                adapter.debug("End of reset", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def check_number_of_items(self):
            """
            Prompts the user to select either a folder (for Picture Bingo)
            or a file (for Word Bingo) and checks the selection for an
            appropriate number of items.

            If an inappropriate number of items is detected, prompt the user
            to add or remove items if there are too few or too many, respectively.
            
            Returns a String of the path to the folder/file.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of check_number_of_items", caller=calframe[1][3])

                if self.bingoType == "pictures":
                    self.bingoTypePopup = self.popup("Now choose the folder that contains the pictures to use.", button1Text="Ok")
                    # Prompt the user for a folder of images to use.
                    while True:
                        folder = filedialog.askdirectory(title="Select the folders the pictures are in")
                        if not folder:
                            adapter.debug("    Returning False")
                            adapter.debug("End of check_number_of_items")
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

                    adapter.debug("    Returning " + folder)
                    adapter.debug("End of check_number_of_items")
                    return folder
                elif self.bingoType == "words":
                    self.bingoTypePopup = self.popup("Now choose the file that contains the words to use.", button1Text="Ok")
                    while True:
                        # Prompt the user for a file that contains the words to use.
                        file = filedialog.askopenfilename(title="Select the file the words are in.", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
                        if not file:
                            adapter.debug("    Returning False")
                            adapter.debug("End of check_number_of_items")
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

                    adapter.debug("    Returning " + file)
                    adapter.debug("End of check_number_of_items")
                    return file
            except Exception as e:
                adapter.exception(e)
                raise


        def get_number_of_cards(self):
            """
            Prompts the user to enter the number of Bingo cards they wish to create.
            Returns an Integer of the number of cards.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of get_number_of_cards", caller=calframe[1][3])

                # Prompt the user to enter the number of cards they want to create.
                # Must be a positive whole number.
                while True:
                    self.cardsPopup = self.popup("Enter the number of Bingo cards to generate.", entry=True, button1Text="Ok")
                    
                    try:
                        cards = int(self.cardsPopup.value)
                    except ValueError:
                        self.popup("It has to be a positive whole number!", button1Text="Ok")
                        continue
                    except:
                        raise

                    if cards <= 0:
                        self.popup("You need at least one card!", button1Text="Ok")
                        continue

                    break

                adapter.debug("    Returning " + str(cards))
                adapter.debug("End of get_number_of_cards")
                return cards
            except Exception as e:
                adapter.exception(e)
                raise


        def create_bingo_cards(self, freeSpace, cards):
            """
            Creates the individual Bingo cards.

            Requird Parameters:
                freeSpace: Boolean
                    Whether to have the central square in each card be a "free space".

                cards: Integer
                    The number of Bingo cards to create.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of create_bingo_cards: freeSpace=" + str(freeSpace) + ", cards=" + str(cards), caller=calframe[1][3])
                
                # Since I don't know how long this could take, display a progress bar.
                self.progressLabel = tk.Label(root, text="Creating bingo cards..")
                self.progressLabel.place(relx=0.50, rely=0.82, anchor=tk.CENTER)
                self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode="determinate")
                self.progress.place(relx=0.50, rely=0.80, anchor=tk.CENTER)
                self.progress["value"] = 0

                for c in range(cards):
                    self.progress["value"] = ((c + 1) / cards) * 100
                    root.update_idletasks()
                    # Create a card.
                    self.generate_html_card(c, freeSpace)

                # Ditch the progress bar.
                self.progress.place_forget()
                self.progressLabel.place_forget()

                adapter.debug("End of create_bingo_cards", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def create_new_bingo_file(self, bingoType, gameExists):
            """
            Creates a new set of bingo cards.

            Required Parameters:
                bingoType: String
                    The type of bingo cards to create (words or pictures).

                gameExists: Boolean
                    Whether this method was called to create more cards from the same source.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of create_new_bingo_file: bingoType=" + str(bingoType), caller=calframe[1][3])

                if not gameExists:
                    # Check to see if we're interrupting a game by doing this.
                    if self.gameInProgress and not self.interrupt_confirm():
                        adapter.debug("End of create_new_bingo_file (nothing done)")
                        return

                    # Reset everything.
                    self.reset()

                    # Save a .bingo file to store the locations of important files in the working_dir folder.
                    self.bingoFile = self.save_bingo_file()

                    # If we chose not to save, reset everything and return.
                    if not self.bingoFile:
                        self.reset()
                        adapter.debug("End of create_new_bingo_file (nothing done)")
                        return

                    self.bingoType = bingoType

                    # Prompt the user to select a file for word Bingo or a folder for picture Bingo.
                    # For words, check the number of lines in the file.
                    # For pictures, check the number of files in the folder.
                    items = self.check_number_of_items()

                    # If we didn't select a file/folder, reset and return.
                    if not items:
                        self.reset()
                        adapter.debug("End of create_new_bingo_file")
                        return

                    # Create a folder named after the .bingo file under the working_dir folder.
                    # This is where the relevant files for this Bingo game will live.
                    workingDirName = os.path.splitext(os.path.basename(self.bingoFile))[0]
                    self.bingoFullPath = os.path.dirname(__file__) + "\\working_dir\\" + workingDirName
                else:
                    if not self.more_cards_confirm():
                        adapter.debug("End of create_new_bingo_file (nothing done)")
                        return

                # Delete existing files/folders.
                self.delete_unused_files_folders(self.bingoFullPath + ("\\bingo_cards" if gameExists else ""))
                        
                if not os.path.exists(self.bingoFullPath + "\\bingo_cards"):
                    adapter.debug("Creating " + str(self.bingoFullPath + "\\bingo_cards"))
                    os.makedirs(self.bingoFullPath + "\\bingo_cards")

                if not gameExists:
                    # Create subfolders to house the different sizes of pictures.
                    if bingoType == "pictures":
                        if not os.path.exists(self.bingoFullPath + "\\card_pictures"):
                            adapter.debug("Creating " + str(self.bingoFullPath + "\\card_pictures"))
                            os.makedirs(self.bingoFullPath + "\\card_pictures")
                        if not os.path.exists(self.bingoFullPath + "\\display_pictures"):
                            adapter.debug("Creating " + str(self.bingoFullPath + "\\display_pictures"))
                            os.makedirs(self.bingoFullPath + "\\display_pictures")
                        if not os.path.exists(self.bingoFullPath + "\\history_pictures"):
                            adapter.debug("Creating " + str(self.bingoFullPath + "\\history_pictures"))
                            os.makedirs(self.bingoFullPath + "\\history_pictures")

                # Prompt the user for the number of Bingo cards they want to create.
                cards = self.get_number_of_cards()

                # Prompt the user for whether they want a "FREE SPACE" in the middle square in each card.
                self.freeSpacePopup = self.popup("Do want a free space in the middle square?", button1Text="Yes", button2Text="No")

                if not gameExists:
                    if self.bingoType == "pictures":
                        # Since I don't know how long this could take, display a progress bar.
                        self.progressLabel = tk.Label(root, text="Processing images..")
                        self.progressLabel.place(relx=0.50, rely=0.82, anchor=tk.CENTER)
                        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode="determinate")
                        self.progress.place(relx=0.50, rely=0.80, anchor=tk.CENTER)
                        self.progress["value"] = 0
                        
                        # Create the necessary files for picture Bingo:
                        for i, picture in enumerate(self.pictures):
                            self.progress["value"] = ((i + 1) / len(self.pictures)) * 100
                            root.update_idletasks()

                            # Medium images to be in the bingo cards.
                            newCardPicture = self.resize_image(items, self.bingoFullPath, picture, i, "card", 150)
                            if not newCardPicture:
                                self.reset()
                                adapter.debug("End of create_new_bingo_file")
                                adapter.debug("    Returning after reset")
                                return
                            
                            self.cardPictures.append(newCardPicture)
                            
                            # Small images to be in the history during play.
                            newHistoryPicture = self.resize_image(items, self.bingoFullPath, picture, i, "history", 50)
                            if not newHistoryPicture:
                                self.reset()
                                adapter.debug("End of create_new_bingo_file")
                                adapter.debug("    Returning after reset")
                                return
                            
                            self.historyPictures.append(newHistoryPicture)
                            
                            # Large images for display when you click the "Display next item" button.
                            newDisplayPicture = self.resize_image(items, self.bingoFullPath, picture, i, "display", 350)
                            if not newDisplayPicture:
                                self.reset()
                                adapter.debug("End of create_new_bingo_file")
                                adapter.debug("    Returning after reset")
                                return
                            
                            self.displayPictures.append(newDisplayPicture)

                        # Ditch the progress bar.
                        self.progress.place_forget()
                        self.progressLabel.place_forget()

                self.create_bingo_cards(self.freeSpacePopup, cards)

                # Save the dict again.
                self.save_dict_file(self.bingoFile)

                # Everything should be set to go!
                self.prep_for_play()

                adapter.debug("End of create_new_bingo_file", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise
            

        def prep_for_play(self):
            """
            Randomizes the lists of display items for playing Bingo.
            Enables the button/menu item to view the bingo cards
            and display the next image or word.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of prep_for_play", caller=calframe[1][3])

                # Randomize the lists that will be displayed when you click the "Display next item" button.
                random.shuffle(self.displayPictures)
                random.shuffle(self.words)

                gameMenu.entryconfig("Display next item", state=tk.NORMAL)
                gameMenu.entryconfig("Save bingo cards to PDF", state=tk.NORMAL)
                gameMenu.entryconfig("New bingo cards", state=tk.NORMAL)
                
                self.rightBindId = enable_binding("Right", lambda x: self.keybind_call("Right"))
                self.sBindId = enable_binding("Control-s", lambda x: self.keybind_call("s"))
                self.cBindId = enable_binding("Control-c", lambda x: self.keybind_call("c"))

                self.nextItem["state"] = tk.NORMAL
                self.saveBingoCards["state"] = tk.NORMAL

                adapter.debug("End of prep_for_play", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def load_bingo_game(self):
            """
            Loads a .bingo card fore viewing and/or playing.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of load_bingo_game", caller=calframe[1][3])

                # Check to see if there's already a game in progress.
                if not self.interrupt_confirm():
                    adapter.debug("End of load_bingo_game (nothing done)")
                    return

                self.reset()

                # Get a .bingo file to play.
                self.bingoFile = self.load_bingo_file()
                if not self.bingoFile:
                    adapter.debug("End of load_bingo_game (nothing done)")
                    return

                # Set everything up!
                self.prep_for_play()
                self.display_next_item()

                adapter.debug("End of load_bingo_game", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def display_next_item(self):
            """
            Displays the next item in the randomized list of items while playing Bingo.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of display_next_item", caller=calframe[1][3])

                self.gameInProgress = True
                
                self.nBindId = enable_binding("Control-n", lambda x: self.keybind_call("n"))
                self.newGame["state"] = tk.NORMAL
                gameMenu.entryconfig("New Game", state=tk.NORMAL)

                if len(self.calledItems) > 0:
                    self.leftBindId = enable_binding("Left", lambda x: self.keybind_call("Left"))
                    self.previousItem["state"] = tk.NORMAL
                    gameMenu.entryconfig("Display previous item", state=tk.NORMAL)

                # Remove the instructions if they're on screen.
                if self.startText:
                    canvas.delete(self.startText)
                
                if self.bingoType == "pictures":
                    # This helps determine where the history images are displayed on screen.
                    # Needs to be calculated prior to self.calledItems changing.
                    self.xOffset = 52 * floor(len(self.calledItems) / 5)
                    self.yOffset = 50 * (len(self.calledItems) % 5)
                    
                    # Get the next image.
                    calledItem = self.displayPictures.pop()
                    self.calledItems.append(calledItem)
                    img = ImageTk.PhotoImage(Image.open(calledItem))

                    # If an image has already been displayed, delete it so we're not just piling images on top of one another.
                    if len(self.calledItems) > 1:
                        canvas.delete(self.displayCanvas)

                    # Display the image.
                    self.displayCanvas = canvas.create_image(500, 625, anchor=tk.S, image=img)
                    canvas.image = img

                    # Put the called images into the history.
                    hImg = ImageTk.PhotoImage(Image.open(calledItem.replace("/display_pictures/", "/history_pictures/")))
                    hi = tk.Label(image=hImg)
                    hi.image = hImg

                    # Place this image at x,y coordinates on screen, starting near the top left,
                    # going across the screen to the right, then starting a new row.
                    hi.place(x=5 + self.xOffset, y=10 + self.yOffset)
                    self.displayedHistoryPictures.append(hi)
                else:
                    # Display the next word.
                    self.calledItems.append(self.words.pop())
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
                if (self.bingoType == "pictures" and len(self.displayPictures) == 0) or (self.bingoType == "words" and len(self.words) == 0):
                    self.popup("That's all the " + self.bingoType + ". Someone better have a Bingo by now!", button1Text="Ok")
                    self.nextItem["state"] = tk.DISABLED
                    gameMenu.entryconfig("Display next item", state=tk.DISABLED)
                    self.gameInProgress = False

                adapter.debug("End of display_next_item", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


        def display_previous_item(self):
            """
            A "go back" button to use while playing Bingo.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of display_previous_item", caller=calframe[1][3])

                self.gameInProgress = True

                if self.bingoType == "pictures":
                    # Get the previous image.
                    previousItem = self.calledItems.pop()
                    self.displayPictures.append(previousItem)
                    img = ImageTk.PhotoImage(Image.open(self.calledItems[-1]))

                    canvas.delete(self.displayCanvas)

                    # Display the image.
                    self.displayCanvas = canvas.create_image(500, 625, anchor=tk.S, image=img)
                    canvas.image = img
                    
                    # Remove the current image from the history.
                    previousHistoryItem = self.displayedHistoryPictures.pop()
                    previousHistoryItem.place_forget()
                else:
                    # Display the last word.
                    previousItem = self.calledItems.pop()
                    self.words.append(previousItem)
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

                if len(self.calledItems) < 2:
                    self.leftBindId = enable_binding("Left", do_nothing)
                    self.previousItem["state"] = tk.DISABLED
                    gameMenu.entryconfig("Display previous item", state=tk.DISABLED)

                if self.nextItem["state"] == tk.DISABLED:
                    self.rightBindId = enable_binding("Right", lambda x: self.keybind_call("Right"))
                    self.nextItem["state"] = tk.NORMAL
                    gameMenu.entryconfig("Display next item", state=tk.NORMAL)

                adapter.debug("End of display_previous_image", caller=calframe[1][3])
            except:
                adapter.exception("message")
                raise
                   

        def create_buttons(self):
            """
            Create the buttons for displaying the next/last item while playing Bingo.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of create_buttons", caller=calframe[1][3])

                if not hasattr(self, "Save bingo cards to PDF"):
                    self.saveBingoCards = ttk.Button(self)
                    self.saveBingoCards["text"] = "Save bingo cards to PDF"
                    self.saveBingoCards["command"] = self.save_bingo_cards
                    self.saveBingoCards.pack({"side": "left"}, padx=100)
                    self.saveBingoCards["state"] = tk.DISABLED
                    self.buttons.add(self.saveBingoCards)

                if not hasattr(self, "previousItem"):
                    self.previousItem = ttk.Button(self)
                    self.previousItem["text"] = "Previous item"
                    self.previousItem["command"] = self.display_previous_item
                    self.previousItem.pack({"side": "left"}, padx=(0, 10))
                    self.previousItem["state"] = tk.DISABLED
                    self.buttons.add(self.previousItem)

                if not hasattr(self, "nextItem"):
                    self.nextItem = ttk.Button(self)
                    self.nextItem["text"] = "Next item"
                    self.nextItem["command"] = self.display_next_item
                    self.nextItem.pack({"side": "left"})
                    self.nextItem["state"] = tk.DISABLED
                    self.buttons.add(self.nextItem)

                if not hasattr(self, "newGame"):
                    self.newGame = ttk.Button(self)
                    self.newGame["text"] = "New Game"
                    self.newGame["command"] = self.new_game
                    self.newGame.pack({"side": "left"}, padx=100)
                    self.newGame["state"] = tk.DISABLED
                    self.buttons.add(self.newGame)

                adapter.debug("End of create_buttons", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise
            

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
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of popup: labelText=" + labelText + ", entry=" + str(entry) + ", button1Text=" + str(button1Text) + ", button2Text=" + str(button2Text), caller=calframe[1][3])
                
                p = PopupWindow(self.master, labelText, entry=entry, button1Text=button1Text, button2Text=button2Text)
                
                # Disable all buttons while the popup is active.
                for b in self.buttons:
                    b["state"] = tk.DISABLED

                # Disable the menus while the popup is active.
                menuBar.entryconfig("File", state=tk.DISABLED)
                menuBar.entryconfig("Game", state=tk.DISABLED)

                # Disable the keyboard shortcuts while the popup is active.
                adapter.debug("Disabling bindings")
                self.wBindId = enable_binding("Control-w", do_nothing)
                self.pBindId = enable_binding("Control-p", do_nothing)
                self.oBindId = enable_binding("Control-o", do_nothing)
                self.nBindId = enable_binding("Control-n", do_nothing)
                self.rightBindId = enable_binding("Right", do_nothing)
                self.sBindId = enable_binding("Control-s", do_nothing)
                self.leftBindId = enable_binding("Left", do_nothing)
                self.cBindId = enable_binding("Control-c", do_nothing)
                    
                self.master.wait_window(p.top)

                # Enable the menus.
                menuBar.entryconfig("File", state="normal")
                menuBar.entryconfig("Game", state="normal")

                # Enable the keyboard shortcuts (and next/previous buttons).
                adapter.debug("Enabling bindings")
                self.wBindId = enable_binding("Control-w", lambda x: self.keybind_call("w"))
                self.pBindId = enable_binding("Control-p", lambda x: self.keybind_call("p"))
                self.oBindId = enable_binding("Control-o", lambda x: self.keybind_call("o"))

                if self.bingoType:
                    self.cBindId = enable_binding("Control-s", lambda x: self.keybind_call("s"))
                    self.cBindId = enable_binding("Control-c", lambda x: self.keybind_call("c"))

                if (self.bingoType == "pictures" and len(self.displayPictures) > 0) or (self.bingoType == "words" and len(self.words) > 0):
                    self.rightBindId = enable_binding("Right", lambda x: self.keybind_call("Right"))
                    self.nextItem["state"] = tk.NORMAL

                if len(self.calledItems) > 1:
                    self.leftBindId = enable_binding("Left", lambda x: self.keybind_call("Left"))
                    self.previousItem["state"] = tk.NORMAL

                if len(self.calledItems) > 0:
                    self.nBindId = enable_binding("Control-n", lambda x: self.keybind_call("n"))
                    self.newGame["state"] = tk.NORMAL

                adapter.debug("    Returning")
                adapter.debug("End of popup")
                return p
            except Exception as e:
                adapter.exception(e)
                raise


        def keybind_call(self, call, event=None):
            """
            Keyboard shortcut for creating a new set of word bingo cards.

            Required Parameters:
                call: String
                    The keybind activated.

            Optional Parameters:
                event: tkinter.Event
                    The tkinter Event that is the trigger.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of ctrl_w", caller=calframe[1][3])

                if call == "w":
                    self.create_new_bingo_file(bingoType="words", gameExists=False)
                elif call == "p":
                    self.create_new_bingo_file(bingoType="pictures", gameExists=False)
                elif call == "c":
                    self.create_new_bingo_file(bingoType=self.bingoType, gameExists=True)
                elif call == "o":
                    self.load_bingo_game()
                elif call == "q":
                    root.quit()
                elif call == "n":
                    self.new_game()
                elif call == "s":
                    self.save_bingo_cards()
                elif call == "Right":
                    self.display_next_item()
                elif call == "Left":
                    self.display_previous_item()

                adapter.debug("End of ctrl_w", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise
        

    class PopupWindow(object):
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
            try:
                top = self.top = tk.Toplevel(master)
                top.wait_visibility()
                top.grab_set_global()
                self.l = tk.Label(top, text=labelText, font=("calibri", 16))
                self.l.pack()
                self.l.focus_force()

                if entry:
                    self.e = tk.Entry(top, font=("calibri", 16))
                    self.e.pack()
                    self.e.focus_force()

                if button1Text:
                    if entry:
                        self.b1 = tk.Button(top, text=button1Text, font=("calibri", 16), command=lambda x: self.cleanup("entry"))
                    else:
                        self.b1 = tk.Button(top, text=button1Text, font=("calibri", 16), command=lambda x: self.cleanup(True))
                        
                    if entry:
                        enable_binding("Return", lambda x: self.cleanup("entry"))
                    elif button1Text in ["Ok", "Yes"]:
                        enable_binding("Return", lambda x: self.cleanup(True))
                        if button1Text == "Yes":
                            enable_binding("y", lambda x: self.cleanup(True))

                    self.b1.pack()

                if button2Text:
                    self.b2 = tk.Button(top, text=button2Text, font=("calibri", 16), command=lambda x: self.cleanup(False))
                    if button2Text == "No":
                        enable_binding("Escape", lambda x: self.cleanup(False))
                        enable_binding("n", lambda x: self.cleanup(False))

                    self.b2.pack()
            except Exception as e:
                adapter.exception(e)
                raise
            
            
        def cleanup(self, type, event=None):
            """
            Sets the "value" of the popup window object to True and removes the popup window.

            Required Parameters:
                type: String or Boolean
                    Indicates what the popup window value will be set to.
                    If "entry", the value of the entry box.
                    If Boolean, the Boolean.
            """
            try:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                adapter.debug("Start of cleanup", caller=calframe[1][3])

                if type == "entry":
                    self.value = self.e.get()
                else:
                    self.value = type

                adapter.debug("    Cleaning up popup with value of " + str(self.value))
                enable_binding("Return", do_nothing)
                enable_binding("Escape", do_nothing)
                enable_binding("y", do_nothing)
                enable_binding("n", do_nothing)
                self.top.destroy()
                adapter.debug("End of cleanup", caller=calframe[1][3])
            except Exception as e:
                adapter.exception(e)
                raise


    adapter.debug("Start")

    fileFolderDict = {}

    # If the working_dir folder doesn't exist, create it.
    if not os.path.exists(os.path.dirname(__file__) + "//working_dir"):
        adapter.debug("Creating working_dir folder")
        os.makedirs(os.path.dirname(__file__) + "//working_dir")

    # If the fileFolderDict.p file doesn't exist, create it with an empty dictionary.
    if not os.path.exists(os.path.dirname(__file__) + "//fileFolderDict.p"):
        adapter.debug("Creating default fileFolderDict.p")
        pickle.dump(fileFolderDict, open(os.path.dirname(__file__) + "//fileFolderDict.p", "wb"), -1)

    # Load the data in fileFolderDict.p.
    if os.path.getsize("fileFolderDict.p") > 0:
        adapter.debug("Loading fileFolderDict.p")
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
    3. Follow remaining instructions.
    4. Now you can play!

    To play Bingo:
    1. If you created the Bingo cards previously, click File --> Load Bingo button.
    2. Open a .bingo file you created.
    3. Click the \"Display next item\" button until someone wins!"""

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
    root.title("Bingo Generator")
    root.option_add("*tearOff", False)
    root.tk.call("source", os.path.dirname(os.path.realpath(__file__)) + "\\azure.tcl")
    style = ttk.Style(root)
    style.theme_use("azure")
    root.geometry("1000x700")
    canvas = tk.Canvas(root, width = 1000, height = 650)
    canvas.pack()
    root.resizable(False, False)
    app = Application(master=root)
    menuBar = tk.Menu(root)
    fileMenu = tk.Menu(menuBar, tearoff=0)
    gameMenu = tk.Menu(menuBar, tearoff=0)
    fileMenu.add_command(label="New word bingo cards", command=lambda: app.create_new_bingo_file(bingoType="words", gameExists=False), accelerator="Ctrl+W")
    fileMenu.add_command(label="New picture bingo cards", command=lambda:app.create_new_bingo_file(bingoType="pictures", gameExists=False), accelerator="Ctrl+P")
    fileMenu.add_command(label="Load bingo file", command=app.load_bingo_game, accelerator="Ctrl+O")
    fileMenu.add_separator()
    fileMenu.add_command(label="Quit", command=root.quit, accelerator="Ctrl+Q")

    gameMenu.add_command(label="New Game", command=lambda: app.new_game(), state=tk.DISABLED, accelerator="Ctrl+N")
    gameMenu.add_command(label="Display next item", command=lambda: app.display_next_item(), state=tk.DISABLED, accelerator="Right Arrow")
    gameMenu.add_command(label="Display previous item", command=lambda: app.display_previous_item(), state=tk.DISABLED, accelerator="Left Arrow")
    gameMenu.add_separator()
    gameMenu.add_command(label="New bingo cards", command=lambda: app.create_new_bingo_file(bingoType=app.bingoType, gameExists=True), state=tk.DISABLED, accelerator="Ctrl+C")
    gameMenu.add_command(label="Save bingo cards to PDF", command=lambda: app.save_bingo_cards(), state=tk.DISABLED, accelerator="Ctrl+S")

    menuBar.add_cascade(label="File", menu=fileMenu)
    menuBar.add_cascade(label="Game", menu=gameMenu)
    root.config(menu=menuBar)
    app.mainloop()
    adapter.debug("Closing application")
    root.destroy()
except Exception as e:
    error = str(sys.exc_info())
    if "application has been destroyed" not in error:
        raise
