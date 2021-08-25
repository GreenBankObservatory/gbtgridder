#! /usr/bin/env python

# import Python modules that allow us to access system calls
import ast
import os
import sys

from PyQt5.Qt import QApplication, QMainWindow
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt5.uic import *

# define where our .ui file is
dirPath = os.path.dirname(os.path.realpath(__file__))  # dir __file__ is in
qtCreatorFile = dirPath + "/gridder_interface.ui"  # Enter .ui file from Designer here.
output_popupFile = dirPath + "/output_popup.ui"

# load our .ui file
Ui_MainWindow, QtBaseClass = loadUiType(qtCreatorFile)
Ui_OutPop, OutPopBaseClass = loadUiType(output_popupFile)


class OP(QWidget, Ui_OutPop):
    def __init__(self, arguments, the_string):
        """Initialize our controller class."""
        QWidget.__init__(self)
        Ui_OutPop.__init__(self)
        self.setupUi(self)

        # turn off until the oputput is read
        self.buttonOff(self.yesNo_2)

        # begin the gridding
        self.p = None
        self.arguments = [x for x in arguments if x != ""]
        self.the_string = the_string
        self.gridderAction()

        self.yesNo_2.accepted.connect(self.writeInputAccept)
        self.yesNo_2.rejected.connect(self.writeInputReject)

    # set up turning of and on actions for y/n button
    def buttonOn(self, targetBtn):
        targetBtn.setDisabled(False)

    def buttonOff(self, targetBtn):
        targetBtn.setEnabled(False)

    # run the gridder
    def gridderAction(self):
        if self.p is None:  # No process running.
            self.p = (
                QProcess()
            )  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.p.start(
                "gbtgridder", self.arguments
            )  # gridder lives one dir down on dev.

    def process_finished(self):
        self.p = None
        # account for output after either a 'yes' or 'no' response
        self.message(
            "\n \n The gridding program has completed! Please check your output location for your gridded files, or navigate back to the main window to re-run the gridder. \n \n"
        )

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)  # send the sdtout to the output text box

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.bad_message(stderr)  # send the stderr to the error output text box

    def message(self, s):
        self.CL_output.appendPlainText(s)  # display any text to the output text box

    def bad_message(self, k):
        self.CL_error.appendPlainText(k)  # display the errors to the stderr text box

    def writeInputAccept(self):
        self.p.write(b"Yes\n")  # answers the CL input
        self.buttonOff(self.yesNo_2)

    def writeInputReject(self):
        self.p.write(b"No\n")  # answers the CL input
        self.buttonOff(self.yesNo_2)


class App(QMainWindow, Ui_MainWindow):
    """Class to define the application, using .ui file."""

    def __init__(self):
        """Initialize our controller class."""
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.p = None  # for running the gridder

        # connect menus
        self.actionQuit.triggered.connect(self.menuQuit)
        self.actionAbout.triggered.connect(self.menuAbout)
        self.actionSave.triggered.connect(self.saveAction)
        self.actionLoad.triggered.connect(self.loadAction)

        # create names for the buttons
        # dict of the arg name: button link
        self.dict_of_buttons = {
            "check_buttons": {
                "clobber": self.clobber,
                "noline": self.noline,
                "nocont": self.nocont,
                "noweight": self.noweight,
                "nocov": self.nocov,
                "autoConfirm": self.autoConfirm,
            },
            "text_buttons": {
                "pixelwidth": self.pixelwidth,
                "channels": self.channels,
                "outputName": self.outputName,
                "inputFile": self.inputFile,
                "mapcenter": self.mapcenter,
                "size": self.size,
                "average": self.average,
                "scans": self.scans,
                "maxTsys": self.maxTsys,
                "minTsys": self.minTsys,
                "diameter": self.diameter,
                "restfreq": self.restfreq,
                "clonecube": self.clonecube,
            },
            "drop_buttons": {"kernel": self.kernel, "proj": self.proj},
            "slider_buttons": {"verbosity": self.verbosity},
        }

        # dict of the arg name: [flag, default value]
        self.dict_of_values = {
            "check_buttons": {
                "clobber": ["--clobber", ""],
                "noline": ["--noline", ""],
                "nocont": ["--nocont", ""],
                "noweight": ["--noweight", ""],
                "nocov": ["--nocov", ""],
                "autoConfirm": ["--autoConfirm", ""],
            },
            "text_buttons": {
                "pixelwidth": ["--pixelwidth", ""],
                "channels": ["--channels", ""],
                "outputName": ["-o", ""],
                "inputFile": ["", "ENTER INPUT FILES"],
                "mapcenter": ["--mapcenter", ""],
                "size": ["--size", ""],
                "average": ["-a", ""],
                "scans": ["--scans", ""],
                "maxTsys": ["--maxTsys", ""],
                "minTsys": ["--minTsys", ""],
                "diameter": ["--diameter", " 100"],
                "restfreq": ["--restfreq", ""],
                "clonecube": ["--clonecube", ""],
            },
            "drop_buttons": {
                "kernel": ["--kernel", " gaussbessel"],
                "proj": ["--proj", " SFL"],
            },
            "slider_buttons": {"verbosity": ["--verbose", ""]},
        }

        # connect buttons
        self.makeString.clicked.connect(
            self.makeStringAction
        )  # put all the peices together

        self.gridderStart.clicked.connect(self.gridderAction)

        # save and load
        self.save_button.clicked.connect(self.saveAction)
        self.load_button.clicked.connect(self.loadAction)

    def menuQuit(self):
        """Method to handle the quit menu."""
        print("Thanks for using the Gridder")
        sys.exit()

    def closeEvent(self, event):
        """When main window is closed, it calls this method."""
        self.menuQuit()

    def menuAbout(self):
        """Shows about message box."""
        QMessageBox.about(
            self,
            "The GBTGridder",
            "The GBTGridder creates images from GBT SDFITS data. \n\n See http://docs.greenbankobservatory.org/repos/gbtgridder/docs/source/index.html?highlight=gridder for more information. \n\n All widgets have argument information, please hover over any widget box on the window to see more information specific to each argument.",
        )

    def makeStringAction(self):
        self.the_list = []  # clear the list before adding again
        self.the_string = ""  # clear the string before adding again
        # run all the actions to collect data from each button type
        for key in self.dict_of_buttons["check_buttons"]:
            self.checkAction(key)
            # need special declaring for checks because they are only flags; no values
            indx = "check_buttons"
            if self.dict_of_values[indx][key][1] != "":
                self.the_list.extend([self.dict_of_values[indx][key][1]])
            if not self.dict_of_values[indx][key][1] == "":
                self.the_string = (
                    self.the_string + " " + self.dict_of_values[indx][key][1]
                )
        for key in self.dict_of_buttons["text_buttons"]:
            self.textAction(key)
        for key in self.dict_of_buttons["drop_buttons"]:
            self.dropAction(key)
        for key in self.dict_of_buttons["slider_buttons"]:
            self.sliderAction(key)
        # collect all the button's values into one list to be passed to the gbtgridder, or a string to be displayed on the ui
        for indx in ["text_buttons", "drop_buttons", "slider_buttons"]:
            for key in self.dict_of_values[indx]:
                if (
                    self.dict_of_values[indx][key][1] != ""
                ):  # if it is empty we don't care
                    self.the_list.append(str(self.dict_of_values[indx][key][0]))
                    space = (
                        "" if key == "inputFile" and self.the_string == "" else " "
                    )  # the first arg needs no space, the rest do
                    self.the_string = (
                        self.the_string + space + self.dict_of_values[indx][key][0]
                    )
                    if (
                        type(self.dict_of_values[indx][key][1]) == list
                    ):  # if there are >1 args to be passed for one flag
                        for i in self.dict_of_values[indx][key][1]:
                            self.the_list.append(i)
                            self.the_string = self.the_string + space + i
                    else:
                        self.the_list.append(
                            str(self.dict_of_values[indx][key][1])
                        )  # otherwise just add the values to the list or string
                        self.the_string = (
                            self.the_string
                            + space
                            + str(self.dict_of_values[indx][key][1])
                        )
        self.setCLString(self.the_string)  # display the string to the ui

    def setCLString(self, text):  # display a string to the output box of the ui
        self.CLString.clear()
        self.CLString.insertPlainText(text)

    def checkAction(self, button):  # actions to get data from all QCheckbox widgets
        indx = "check_buttons"
        if self.dict_of_buttons[indx][
            button
        ].isChecked():  # if checked populate, if not clear the argument
            self.dict_of_values[indx][button][1] = self.dict_of_values[indx][button][0]
        else:
            self.dict_of_values[indx][button][1] = ""

    def textAction(self, button):  # actions to get data from all QLineEdit widgets
        indx = "text_buttons"
        if (
            self.dict_of_buttons[indx][button].text() == ""
        ):  # need to account for empty and >2 args
            self.dict_of_values[indx][button][1] = ""
        else:
            self.dict_of_values[indx][button][1] = (
                self.dict_of_buttons[indx][button].text().split(" ")
            )

    def dropAction(self, button):  # actions to get data from all QComboBox widgets
        indx = "drop_buttons"
        self.dict_of_values[indx][button][1] = self.dict_of_buttons[indx][
            button
        ].currentText()

    def sliderAction(
        self, button
    ):  # actions to get data from all QSlider widgets (only verosity)
        indx = "slider_buttons"
        self.dict_of_values[indx][button][1] = self.dict_of_buttons[indx][
            button
        ].value()

    def gridderAction(self):  # if the user clicks the button to grid in the ui
        self.makeStringAction()  # get the most up-to-date list of arguments
        self.arguments = self.the_list
        self.gridderWindow = OP(
            self.arguments, self.the_string
        )  # run the widget window for gridding
        self.gridderWindow.show()  # display the widget window

    def saveAction(self):
        name, filetype = QFileDialog.getSaveFileName(
            self, "Save File"
        )  # get the name from fancy QFileDialog
        if name:  # if the user cancels the program won't crash
            file = open(str(name), "w")
            self.makeStringAction()  # make sure we have the most up to date values before saving
            file.write(str(self.dict_of_values))  # only need to save this dict
            file.close()

    def loadAction(self):
        name, filetype = QFileDialog.getOpenFileName(
            self, "Open File"
        )  # get the name from fancy QFileDialog
        if name:  # if the user cancels the program won't crash
            file = open(str(name), "r")
            contents = file.read()
            dictionary = ast.literal_eval(
                contents
            )  # don't want to treat the dict like a string
            file.close()
            self.dict_of_values = (
                dictionary  # re-set all the values in the ui to match the loaded dict
            )
            # re-load the ui values for each of the widget types
            for button in self.dict_of_buttons["text_buttons"]:
                value = ""
                self.dict_of_buttons["text_buttons"][button].clear()
                if (
                    type(self.dict_of_values["text_buttons"][button][1]) == list
                ):  # >2 args need to be seperate with spaces
                    value = " ".join(
                        [
                            str(elem)
                            for elem in self.dict_of_values["text_buttons"][button][1]
                        ]
                    )
                else:
                    value = self.dict_of_values["text_buttons"][button][
                        1
                    ]  # else just display the dict value
                self.dict_of_buttons["text_buttons"][button].insert(value)
            for button in self.dict_of_buttons["check_buttons"]:
                if self.dict_of_values["check_buttons"][button][1] == "":
                    self.dict_of_buttons["check_buttons"][button].setChecked(False)
                else:
                    self.dict_of_buttons["check_buttons"][button].setChecked(True)
            for button in self.dict_of_buttons["drop_buttons"]:
                self.dict_of_buttons["drop_buttons"][button].setCurrentText(
                    self.dict_of_values["drop_buttons"][button][1]
                )
            for button in self.dict_of_buttons["slider_buttons"]:
                # can't have an empty slider value so default it to 4 or else use the user's loaded-in value
                if self.dict_of_values["slider_buttons"][button][1] == "":
                    self.self.dict_of_buttons["slider_buttons"][button].setValue(
                        "4"
                    )  # default is 4
                else:
                    self.dict_of_buttons["slider_buttons"][button].setValue(
                        int(self.dict_of_values["slider_buttons"][button][1])
                    )


if __name__ == "__main__":
    # create an instance of our controller class, and display it
    app = QApplication(sys.argv)
    window = App()
    window.show()

    # start the PyQt even loop; when it finishes, exit
    sys.exit(app.exec_())
