# This python autopsy module will export all files including their slack space and then call
# the command line version of the foremost file carving tool written by Jesse Kornblum, Kris Kendell and Nick Mikus
# and carve for jpgs, bmps, gifs and pngs that maybe embedded in the file. The results are subsequently imported back into autopsy
# as derived files of the parent file where they were carved from.
#
# Contact: alan.browne75@gmail.com
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# FileCarver module to carve jpgs, bmps, gifs and pngs embedded in various files.
# August 2020
# 
# Comments 
#   Version 1.0 - Initial version - August 24, 2020
#   Version 1.1 - Added GUI to include default mime types, all files or slack space - Aug 27, 2020
#   version 1.2 - Added Linux Support - August 30, 2020
# 

import jarray
import inspect
import os
import subprocess
import shutil
from subprocess import Popen, PIPE

from javax.swing import JCheckBox
from javax.swing import JLabel
from javax.swing import JList
from javax.swing import JTextArea
from javax.swing import BoxLayout
from java.awt import GridLayout
from java.awt import BorderLayout
from javax.swing import BorderFactory
from javax.swing import JToolBar
from javax.swing import JPanel
from javax.swing import JFrame
from javax.swing import JScrollPane
from javax.swing import JComponent
from java.awt.event import KeyListener
from java.awt.event import KeyEvent
from java.awt.event import KeyAdapter
from javax.swing.event import DocumentEvent
from javax.swing.event import DocumentListener


from java.lang import Class
from java.lang import System
from java.sql  import DriverManager, SQLException
from java.util.logging import Level
from java.io import File
from org.sleuthkit.datamodel import SleuthkitCase
from org.sleuthkit.datamodel import AbstractFile
from org.sleuthkit.datamodel import ReadContentInputStream
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import GenericIngestModuleJobSettings
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettingsPanel
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.coreutils import PlatformUtil
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import Services
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.casemodule.services import Blackboard
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleContentEvent

# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the analysis.
class CarverFilesIngestModuleFactory(IngestModuleFactoryAdapter):

    def __init__(self):
        self.settings = None

    moduleName = "FileCarver"
    
    def getModuleDisplayName(self):
        return self.moduleName
    
    def getModuleDescription(self):
        return "Carves Images embedded in files"
    
    def getModuleVersionNumber(self):
        return "1.3"

    def getDefaultIngestJobSettings(self):
        return GenericIngestModuleJobSettings()


    def hasIngestJobSettingsPanel(self):
        return True

    # TODO: Update class names to ones that you create below
    def getIngestJobSettingsPanel(self, settings):
        if not isinstance(settings, GenericIngestModuleJobSettings):
            raise IllegalArgumentException("Expected settings argument to be instanceof GenericIngestModuleSettings")
        self.settings = settings
        return NEWProcess_AmcacheWithUISettingsPanel(self.settings)    
    
    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        return CarverFilesIngestModule(self.settings)

# Data Source-level ingest module.  One gets created per data source.
class CarverFilesIngestModule(DataSourceIngestModule):

    
    _logger = Logger.getLogger(CarverFilesIngestModuleFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self, settings):
        self.context = None
        self.local_settings = settings
        self.List_Of_tables = []

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    def startUp(self, context):
        self.context = context

        # Get path to EXE based on where this script is run from.
        # Assumes EXE is in same folder as script
        # Verify it is there before any ingest starts
 

        if PlatformUtil.isWindowsOS():
            self.path_to_exe_foremost = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foremost.exe")
            if not os.path.exists(self.path_to_exe_foremost):
                raise IngestModuleException("Windows Executable was not found in module folder")
        elif PlatformUtil.getOSName() == 'Linux':
            self.path_to_exe_foremost = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foremost')
            if not os.path.exists(self.path_to_exe_foremost):
                raise IngestModuleException("Linux Executable was not found in module folder")
            
            
        if self.local_settings.getSetting('Default_Mime_Types') == 'true':
            self.List_Of_tables.append('Default_Mime_Types')
        if self.local_settings.getSetting('All_Mime_Types') == 'true':
            self.List_Of_tables.append('All_Mime_Types')
        if self.local_settings.getSetting('Include_Slack_Space') == 'true':
            self.List_Of_tables.append('Include_Slack_Space')

		
        #self.logger.logp(Level.INFO, Process_EVTX1WithUI.__name__, "startUp", str(self.List_Of_Events))
        self.log(Level.INFO, str(self.List_Of_tables) + " >> " + str(len(self.List_Of_tables)))

        if "Default_Mime_Types" in self.List_Of_tables:
            self.mimeTypesToFind =  ["application/octet-stream","application/x-sqlite3", "application/vnd.ms-excel.sheet.4",  "application/x-msoffice","application/msword", "application/msoffice", "application/vnd.ms-excel", "application/vnd.ms-powerpoint" ]

        
        # Throw an IngestModule.IngestModuleException exception if there was a problem setting up
        # raise IngestModuleException(IngestModule(), "Oh No!")
        pass

    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # See: http://www.sleuthkit.org/sleuthkit/docs/jni-docs/interfaceorg_1_1sleuthkit_1_1datamodel_1_1_content.html
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    # See: http://sleuthkit.org/autopsy/docs/api-docs/3.1/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_data_source_ingest_module_progress.html
    def process(self, dataSource, progressBar):
	
        moduleName = CarverFilesIngestModuleFactory.moduleName	
        if len(self.List_Of_tables) < 1:
            message = IngestMessage.createMessage(IngestMessage.MessageType.DATA, "FileCarver", " No Mime Types Selected to Parse " )
            IngestServices.getInstance().postMessage(message)
            return IngestModule.ProcessResult.ERROR
        # we don't know how much work there is yet
        progressBar.switchToIndeterminate()
        # Use blackboard class to index blackboard artifacts for keyword search
        blackboard = Case.getCurrentCase().getServices().getBlackboard()

        # For our example, we will use FileManager to get all
        # files with the word "test"
        # in the name and then count and read them
        # FileManager API: http://sleuthkit.org/autopsy/docs/api-docs/latest/classorg_1_1sleuthkit_1_1autopsy_1_1casemodule_1_1services_1_1_file_manager.html
        skCase = Case.getCurrentCase().getSleuthkitCase()
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        if "All_Mime_Types" in self.List_Of_tables:
            files = fileManager.findFiles(dataSource, "%")
            if "Include_Slack_Space" in self.List_Of_tables:
                files=[i for i in files if (i.getSize() > 500)]
                numFiles = len(files)
            else:
                files=[i for i in files if (i.getSize() > 500) and not i.getName().endswith("-slack") ]			
                numFiles = len(files)		
        else:
            files = fileManager.findFilesByMimeType(self.mimeTypesToFind)
            if "Include_Slack_Space" in self.List_Of_tables:
                files=[i for i in files if (i.getSize() > 500)]
                numFiles = len(files)
            else:
                files=[i for i in files if (i.getSize() > 500) and not i.getName().endswith("-slack") ]			
                numFiles = len(files)       

 #       if "Default_Mime_Types" in self.List_Of_tables:
 #           files = fileManager.findFilesByMimeType(self.mimeTypesToFind)
 #           if "Include_Slack_Space" in self.List_Of_tables:
 #               files=[i for i in files if (i.getSize() > 1000)]
 #               numFiles = len(files)
 #           else:
 #               files=[i for i in files if (i.getSize() > 1000) and not i.getName().endswith("-slack") ]			
 #               numFiles = len(files)
 #       else:
 #           files = fileManager.findFiles(dataSource, "%")
 #           if "Include_Slack_Space" in self.List_Of_tables:
 #               files=[i for i in files if (i.getSize() > 1000)]
 #               numFiles = len(files)
 #           else:
 #               files=[i for i in files if (i.getSize() > 1000) and not i.getName().endswith("-slack") ]			
 #               numFiles = len(files)			
		self.log(Level.INFO, "found " + str(numFiles) + " files")
        progressBar.switchToDeterminate(numFiles)
        fileCount = 0
        FileExtractCount=0
        Temp_Dir = Case.getCurrentCase().getModulesOutputDirAbsPath()
        tmp_dir = Case.getCurrentCase().getTempDirectory()
        if PlatformUtil.isWindowsOS():
            self.log(Level.INFO, "create Directory " + Temp_Dir)
            try:
		os.mkdir(Temp_Dir + "\Carved-Foremost")
            except:
                self.log(Level.INFO, "Carved-Foremost Directory already exists " + Temp_Dir)
        else:
            self.log(Level.INFO, "create Directory " + Temp_Dir)
            try:
		os.mkdir(Temp_Dir + "/Carved-Foremost")
            except:
                self.log(Level.INFO, "Carved-Foremost Directory already exists " + Temp_Dir)
        for file in files:

            fileCount += 1

            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK
             

            if ((file.getSize() > 1000) and (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) and (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS) and (file.isFile() != False)):
                self.log(Level.INFO, "Processing file: " + file.getName())

            # Make an artifact on the blackboard.  TSK_INTERESTING_FILE_HIT is a generic type of
            # artfiact.  Refer to the developer docs for other examples.


                fileGetName=file.getName()
				
                if ":" in fileGetName:
                    fileGetName=fileGetName.replace(":","_")
                else:
                    fileGetName=file.getName()
                    if PlatformUtil.isWindowsOS():				
                        out_dir = os.path.join(Temp_Dir + "\Carved-Foremost", str(file.getId()))
                        try:
                           os.mkdir(Temp_Dir + "\Carved-Foremost\\" + str(file.getId()))
                        except:
                           self.log(Level.INFO, str(file.getId()) + " Directory already exists " + Temp_Dir)
                    else:
                        out_dir = os.path.join(Temp_Dir + "/Carved-Foremost", str(file.getId()))
                        try:
                            os.mkdir(Temp_Dir + "/Carved-Foremost/" + str(file.getId()))
                        except:
                            self.log(Level.INFO, str(file.getId()) + " Directory already exists " + Temp_Dir)
                lclDbPath=os.path.join(tmp_dir, str(file.getId()))
                try:
                    ContentUtils.writeToFile(file, File(lclDbPath))
                except:
                    pass
                # Check if output directory exists and if it does then delete it, this may happen with a rerun
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)
		if os.path.exists(lclDbPath):
                    self.log(Level.INFO, "Running prog ==> " + self.path_to_exe_foremost + " -t " + "jpeg,png,bmp,gif" + " -o " + out_dir + " -i " + lclDbPath)
                    pipe = Popen([self.path_to_exe_foremost, "-t" + "jpeg,png,bmp,gif", "-o", out_dir, "-i", lclDbPath], stdout=PIPE, stderr=PIPE)
                    out_text = pipe.communicate()[0]
                    self.log(Level.INFO, "Output from run is ==> " + out_text)
                
                    if len(os.listdir(out_dir)) == 1:
                        shutil.rmtree(out_dir)
			os.remove(lclDbPath)
                    else:
                        art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_INTERESTING_FILE_HIT)
                        att = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_SET_NAME, CarverFilesIngestModuleFactory.moduleName, "New Carved Data and Sqlite Files")
                        art.addAttribute(att)
                        try:
                # index the artifact for keyword search
                            skCase.getBlackboard().postArtifact(art, moduleName)
                        except Blackboard.BlackboardException as e:
                            self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())
                        
                        redactresults = out_dir  
                        auditLog = os.path.join(redactresults,"audit.txt")
                        if os.path.exists(auditLog):
                            os.remove(auditLog)			
                        imagedirs = os.listdir(redactresults)
                        for imagedir in imagedirs:
                            jpgpath=os.path.join(redactresults,imagedir)
                            imagejpgs=os.listdir(jpgpath)
                            for imagejpg in imagejpgs:
                                srcfile=os.path.join(jpgpath,imagejpg)
                                dstfile=os.path.join(redactresults,imagejpg)
                                shutil.move(srcfile,dstfile)
                            shutil.rmtree(jpgpath)
                        extractedfiles = next(os.walk(out_dir))[2]
                        for extractfile in extractedfiles:
                            FileExtractCount=FileExtractCount+1					
                            self.log(Level.INFO, " File Name is ==> " + extractfile)
                            if PlatformUtil.isWindowsOS():
                                 relativeModulepath=Case.getCurrentCase().getModuleOutputDirectoryRelativePath() + "\Carved-Foremost"
                            else:
                                 relativeModulepath=Case.getCurrentCase().getModuleOutputDirectoryRelativePath() + "/Carved-Foremost"
                            relativeCarvedpath=os.path.join(relativeModulepath, str(file.getId())) 
                            relativelocal_file = os.path.join(relativeCarvedpath, extractfile)
                            local_file = os.path.join(out_dir,extractfile)						
                            self.log(Level.INFO, " Local File Name is ==> " + local_file)
               
                            derived_file=skCase.addDerivedFile(extractfile, relativelocal_file, os.path.getsize(local_file), 0, 0, 0, 0, True, file, "", "foremost", "1.5", "", TskData.EncodingType.NONE)
                        
                            IngestServices.getInstance().fireModuleContentEvent(ModuleContentEvent(derived_file))
                        os.remove(lclDbPath)

            # Update the progress bar
            progressBar.progress(fileCount)
            

        #Post a message to the ingest messages in box.
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
            "File Carver Module", "Found %d files" % fileCount)
        IngestServices.getInstance().postMessage(message)

        message2 = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
            "File Carver Module", "Found %d images in %d files " % (FileExtractCount,fileCount))
        IngestServices.getInstance().postMessage(message2)
		
        return IngestModule.ProcessResult.OK              
		
class NEWProcess_AmcacheWithUISettingsPanel(IngestModuleIngestJobSettingsPanel):
    # Note, we can't use a self.settings instance variable.
    # Rather, self.local_settings is used.
    # https://wiki.python.org/jython/UserGuide#javabean-properties
    # Jython Introspector generates a property - 'settings' on the basis
    # of getSettings() defined in this class. Since only getter function
    # is present, it creates a read-only 'settings' property. This auto-
    # generated read-only property overshadows the instance-variable -
    # 'settings'
    
    # We get passed in a previous version of the settings so that we can
    # prepopulate the UI
    # TODO: Update this for your UI
    def __init__(self, settings):
        self.local_settings = settings
        self.initComponents()
        self.customizeComponents()
    
    # TODO: Update this for your UI
    def checkBoxEvent(self, event):
        if self.checkbox.isSelected():
            self.local_settings.setSetting('Default_Mime_Types', 'true')
        else:
            self.local_settings.setSetting('Default_Mime_Types', 'false')
        if self.checkbox1.isSelected():
            self.local_settings.setSetting('All_Mime_Types', 'true')
        else:
            self.local_settings.setSetting('All_Mime_Types', 'false')
        if self.checkbox2.isSelected():
            self.local_settings.setSetting('Include_Slack_Space', 'true')
        else:
            self.local_settings.setSetting('Include_Slack_Space', 'false')


    # TODO: Update this for your UI
    def initComponents(self):
        self.setLayout(BoxLayout(self, BoxLayout.Y_AXIS))
        #self.setLayout(GridLayout(0,1))
        self.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        self.panel1 = JPanel()
        self.panel1.setLayout(BoxLayout(self.panel1, BoxLayout.Y_AXIS))
        self.panel1.setAlignmentY(JComponent.LEFT_ALIGNMENT)
        self.label1 = JLabel("*** Default mime types.")
        self.label2 = JLabel(" ")
        self.label3 = JLabel("octet-stream x-splite3 vnd.ms-excel.sheet.4 msoffice")
        self.label4 = JLabel("msword vnd.ms-excel vnd.ms-powerpoint")
        self.label5 = JLabel(" ")
        self.checkbox = JCheckBox("Default Mime Types Files", actionPerformed=self.checkBoxEvent)
        self.checkbox1 = JCheckBox("All Mime Types Files", actionPerformed=self.checkBoxEvent)
        self.checkbox2 = JCheckBox("Include Slack Space Of Files", actionPerformed=self.checkBoxEvent)
        self.panel1.add(self.label1)
        self.panel1.add(self.label2)
        self.panel1.add(self.label3)
        self.panel1.add(self.label4)
        self.panel1.add(self.label5)
        self.panel1.add(self.checkbox)
        self.panel1.add(self.checkbox1)
        self.panel1.add(self.checkbox2)
        self.add(self.panel1)
		


    # TODO: Update this for your UI
    def customizeComponents(self):
        self.checkbox.setSelected(self.local_settings.getSetting('Default_Mime_Types') == 'true')
        self.checkbox1.setSelected(self.local_settings.getSetting('All_Mime_Types') == 'true')
        self.checkbox2.setSelected(self.local_settings.getSetting('Include_Slack_Space') == 'true')

    # Return the settings used
    def getSettings(self):
        return self.local_settings

 
