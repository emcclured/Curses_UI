#!/usr/bin/python


############### Libraries #################

import npyscreen
import curses
import psycopg2
import sqlite3
import os
import pandas as pd
import pandas as pld
from sqlalchemy import create_engine
from pandas.io import sql
from pandas.io.sql import read_sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

############### Global Variables #####################

# this is the postgresql connections

con = None
adminCon = None

# this is the postgresql db and user info

dbhost = None
dbport = None
dbname = None
dbuser = None
dbpass = None

############### ConnectForm Code #####################

class ConnectButton(npyscreen.ButtonPress):
    def whenPressed(self):
	# set the global variables

	global dbhost
	global dbport
	global dbname
	global dbuser
	global dbpass

	# fill in the fields

        dbhost = self.parent.get_widget('DbHost').value
        dbport = self.parent.get_widget('DbPort').value
        dbname = self.parent.get_widget('DbName').value
        dbuser = self.parent.get_widget('DbUser').value
        dbpass = self.parent.get_widget('DbPass').value

        try:
            # declare and modify the global con

            global con

            con = psycopg2.connect(database=dbname, user=dbuser, password=dbpass, host=dbhost, port=dbport)

        except psycopg2.DatabaseError, e:
            npyscreen.notify_confirm("Could not connect to database!  Please try again!")
            return

        try:
            # declare and modify the global adminCon

            global adminCon

            adminCon = psycopg2.connect(database="postgres", user=dbuser, password=dbpass, host=dbhost, port=dbport)

        except psycopg2.DatabaseError, e:
            npyscreen.notify_confirm("Could not connect to postgres database!  Will not be able to do certain admin functions!")

        self.parent.change_form()


class MainForm(npyscreen.ActionForm):
    def create(self):
        self.add(npyscreen.TitleText, w_id="DbHost", name="Database Host:", begin_entry_at=21, value="0.0.0.0")
        self.add(npyscreen.TitleText, w_id="DbPort", name="Database Port:", begin_entry_at=21, value="5432")
        self.add(npyscreen.TitleText, w_id="DbName", name="Database Name:", begin_entry_at=21, value="vtestdb")
        self.add(npyscreen.TitleText, w_id="DbUser", name="Database User:", begin_entry_at=21, value="vagrant")
        self.add(npyscreen.TitleText, w_id="DbPass", name="Database Password:", begin_entry_at=21, value="vagrant")

        self.add(ConnectButton, name="Connect to Database")

    def on_ok(self):
        self.parentApp.switchForm(None)

    def change_form(self, *args, **keywords):
        name = "EMPTY"

        self.parentApp.change_form(name)

############### SQL StructureEntryForm Code #####################

class ShowAllButton(npyscreen.ButtonPress):
    def whenPressed(self):
        try:
            global con
            cur = con.cursor()
            cur.execute("""SELECT table_name From information_schema.tables WHERE table_schema = 'public'""")
            rows = cur.fetchall()
            outputList = []
            for row in rows:
                outputList.append(row)
            self.parent.get_widget('StructureMenu').values = [val[0] for val in outputList]
            self.parent.get_widget('StructureMenu').display()
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")
        return


class StructureCommandButton(npyscreen.ButtonPress):
    def whenPressed(self):
	selected=self.parent.get_widget('StructureMenu').get_selected_objects()

        try:
            # declare the global con

            global con

            # get current database connection

            cur = con.cursor()

            # execute it

            cur.execute("SELECT ordinal_position, column_name, data_type, collation_name, is_nullable, column_default FROM information_schema.columns WHERE table_name ='" + str(selected[0]) + "'")

            rows = cur.fetchall()

            outputList = []

                # convert the row objects returned into individual strings
            
            outputList.append("|\t#\t| Name\t| Data Type\t| Collation\t| Null\t| Default\t|")
            outputList.append("-----------------------------------------------------")
            for row in rows:
                outputList.append(str(row))
                outputList.append("----------------------------------------------------- ")

                # add strings to the ResultTextBox
            self.parent.get_widget('ResultTextBox').values = outputList

                # now display the values that were added

            self.parent.get_widget('ResultTextBox').display()
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")

            return


class StructureEntryForm(npyscreen.ActionForm):
    def create(self):

	self.show_atx = 22
	self.show_aty = 3

	self.add(ShowAllButton, name="Select Table to View Structure Of")
        self.add(npyscreen.TitleSelectOne, w_id="StructureMenu", name="Table List:", max_height=7, scroll_exit=True, )

	self.add(StructureCommandButton, name="Get Structure of Table")        

	self.add(npyscreen.BoxTitle, w_id="ResultTextBox", name="Structure of Table:", max_height=7,
				   max_width =50,
                                   scroll_exit=True,
                                   contained_widget_arguments={
                                       'color': "WARNING",
                                       'widgets_inherit_color': True, },
                                   )


	#self.dbNumber = self.add(npyscreen.TitleText, name='#')
        #self.varName = self.add(npyscreen.TitleText, name='Name')
        #self.varType = self.add(npyscreen.TitleText, name='Type')
	#self.collation = self.add(npyscreen.TitleText, name='Collation')
        #self.attributes = self.add(npyscreen.TitleText, name='Attributes')
        #self.null = self.add(npyscreen.TitleText, name='Null')
	#self.default = self.add(npyscreen.TitleText, name='Default')
        #self.extra = self.add(npyscreen.TitleText, name='Extra')


    def change_to_admin_form(self, *args, **keywords):
	name = "ADMIN"

        self.parentApp.change_form(name)
	
    def change_to_structure_form(self, *args, **keywords):
	name = "STRUCTURE"

        self.parentApp.change_form(name)

    def change_to_sql_form(self, *args, **keywords):
	name = "SQLENTRY"

        self.parentApp.change_form(name)

    def change_to_browse_form(self, *args, **keywords):
        name = "BROWSE"

        self.parentApp.change_form(name)

    def change_to_import_form(self, *args, **keywords):
	name = "IMPORT"

        self.parentApp.change_form(name)

    def change_to_export_form(self, *args, **keywords):
	name = "EXPORT"

        self.parentApp.change_form(name)

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")


############### SQL SqlEntryForm Code #####################

class SqlCommandButton(npyscreen.ButtonPress):
    def whenPressed(self):
        output_text = self.parent.get_widget('CommandTextBox').values

        try:
            # declare the global con

            global con

            # get current database connection

            cur = con.cursor()

            # execute it

            for value in output_text:
                cur.execute(value)

            con.commit()

            testCommandString = cur.query

            testFirstStringInCommand = testCommandString.partition(' ')[0]

            if (testFirstStringInCommand == 'SELECT'):
                rows = cur.fetchall()

                outputList = []

                # convert the row objects returned into individual strings

                for row in rows:
                    outputList.append(str(row))

                # add strings to the ResultTextBox

                self.parent.get_widget('ResultTextBox').values = outputList

                # now display the values that were added

                self.parent.get_widget('ResultTextBox').display()

	    elif (testFirstStringInCommand == 'DROP'):
		npyscreen.notify_confirm("Table Dropped!")

            else:
                # add testCommandString to the ResultTextBox

                outputList = []

                outputList.append(testCommandString)

                self.parent.get_widget('ResultTextBox').values = outputList

                # now display the values that were added

                self.parent.get_widget('ResultTextBox').display()

        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")

            return


class SqlEntryForm(npyscreen.ActionForm):
    def create(self):

	self.show_atx = 22
	self.show_aty = 3

        self.add(npyscreen.MultiLineEditableBoxed, w_id="CommandTextBox",
                                    name="SQL Command:", max_height=7, max_width=50,
                                    scroll_exit=True, edit=True, )


        self.add(SqlCommandButton, name="Execute SQL Command",)

        self.add(npyscreen.BoxTitle, w_id="ResultTextBox", name="Result:", max_height=7,
				   max_width=50,
                                   scroll_exit=True,
                                   contained_widget_arguments={
                                       'color': "WARNING",
                                       'widgets_inherit_color': True, },
                                   )

    def change_to_admin_form(self, *args, **keywords):
	name = "ADMIN"

        self.parentApp.change_form(name)

    def change_to_structure_form(self, *args, **keywords):
	name = "STRUCTURE"

        self.parentApp.change_form(name)

    def change_to_sql_form(self, *args, **keywords):
	name = "SQLENTRY"

        self.parentApp.change_form(name)

    def change_to_import_form(self, *args, **keywords):
	name = "IMPORT"

        self.parentApp.change_form(name)

    def change_to_export_form(self, *args, **keywords):
	name = "EXPORT"

        self.parentApp.change_form(name)

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

############### Database Tables #######################

def ListTables():
    global con
    cur = con.cursor()
    cur.execute("SELECT datname from pg_database")
    rows = cur.fetchall()
    outputList = []
    for row in rows:
	temp=str(row)
	temp2 = temp.split("'")
	temp3 = temp2[1]
    	
	outputList.append(temp3)

    return outputList

############### Empty Form Code #######################

class RefreshButton(npyscreen.ButtonPress):
    def whenPressed(self):
	outputList = ListTables()
	self.parent.get_widget('DBTableList').values = outputList
        self.parent.get_widget('DBTableList').display()
	return

class AdminButton(npyscreen.ButtonPress):
    def whenPressed(self):
	self.parent.change_to_admin_form()
	return

class StructureButton(npyscreen.ButtonPress):
    def whenPressed(self):
	self.parent.change_to_structure_form()
	return

class SqlButton(npyscreen.ButtonPress):
    def whenPressed(self):
	self.parent.change_to_sql_form()
	return

class BrowseButton(npyscreen.ButtonPress):
    def whenPressed(self):
        self.parent.change_to_browse_form()
	return

class SearchButton(npyscreen.ButtonPress):
    def whenPressed(self):
        self.parent.change_to_search_form()
	return

class ExportButton(npyscreen.ButtonPress):
    def whenPressed(self):
	self.parent.change_to_export_form()
	return

class ImportButton(npyscreen.ButtonPress):
    def whenPressed(self):
	self.parent.change_to_import_form()
	return

class EmptyForm(npyscreen.ActionForm):
    def create(self):
	self.add(npyscreen.BoxTitle, w_id="DBTableList", name = "Databases", rely=2, relx=1, 
		max_width=20, max_height=19, scroll_exit=True, )

	self.add(RefreshButton, name="Refresh DB List", relx=1, rely=21)

	self.add(AdminButton, name="Admin", relx=1, rely=1)
	self.add(StructureButton, name="Structure", relx=12, rely=1)
	self.add(SqlButton, name="SQL", relx=25, rely=1)	
	self.add(BrowseButton, name="Browse", relx=32, rely=1)
	self.add(SearchButton, name="Search", relx=42, rely=1)
	self.add(ExportButton, name="Export", relx=53, rely=1)
	self.add(ImportButton, name="Import", relx=64, rely=1)

    def change_to_admin_form(self, *args, **keywords):
	name = "ADMIN"

        self.parentApp.change_form(name)

    def change_to_structure_form(self, *args, **keywords):
	name = "STRUCTURE"

        self.parentApp.change_form(name)

    def change_to_sql_form(self, *args, **keywords):
	name = "SQLENTRY"

        self.parentApp.change_form(name)

    def change_to_import_form(self, *args, **keywords):
	name = "IMPORT"

        self.parentApp.change_form(name)

    def change_to_export_form(self, *args, **keywords):
	name = "EXPORT"

        self.parentApp.change_form(name)

    def change_to_browse_form(self, *args, **keywords):
        name = "BROWSE"

        self.parentApp.change_form(name)

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm(None)

############### Import Form Code #######################

class GetImportTablesButton(npyscreen.ButtonPress):
    def whenPressed(self):
        global con
        cur = con.cursor()
        cur.execute("""SELECT table_name From information_schema.tables WHERE table_schema = 'public'""")
        rows = cur.fetchall()
        outputList = []

        for row in rows:
            #parse out the table name only

	    temp=str(row)
	    temp2 = temp.split("'")
	    temp3 = temp2[1]

	    outputList.append(temp3)

        self.parent.get_widget('ImportTable').values = outputList
        self.parent.get_widget('ImportTable').display()

	return

class SetImportTableButton(npyscreen.ButtonPress):
    def whenPressed(self):
        selectedLineNumber = self.parent.get_widget('ImportTable').value

	if (selectedLineNumber==None):
	   return;

        outputText = self.parent.get_widget('ImportTable').values[selectedLineNumber]

        self.parent.get_widget('ImportTableText').value = outputText
        self.parent.get_widget('ImportTableText').display()

	return

class GoImportButton(npyscreen.ButtonPress):
    def whenPressed(self):
        try:
	    # get the user input fields

	    tableName = self.parent.get_widget('ImportTableText').value	
	    fileName = self.parent.get_widget('ImportFileText').value

	    if (tableName==""):
		return

	    if (fileName==""):
		return

            # declare the global user and database fields

	    global dbhost
	    global dbport
	    global dbname
	    global dbuser
	    global dbpass

	    engineText = "postgresql+psycopg2://" + dbuser + ":" +dbpass + "@" + dbhost + ":" + dbport + "/" + dbname

	    engine = create_engine(engineText)

	    fileCheck = self.parent.get_widget('ImportCheckBox').value

	    if(fileCheck==1):
    		sql_db = sqlite3.connect(fileName)
		sql_query = "select * from " + tableName
    		df = pld.read_sql_query(sql_query, sql_db)
    		sql_db.close()
	    else:
		df = pd.read_csv(fileName)

	    df.to_sql(tableName, engine, if_exists='replace')

	    outputText = " File: " + fileName + " Imported into Database." 
		
	    npyscreen.notify_confirm(outputText)
	       
        except:
            npyscreen.notify_confirm("Command did not work!  Please try again!")

            return

class ImportForm(npyscreen.ActionForm):
    def create(self):
        self.show_atx=22
        self.show_aty=3
	self.add(npyscreen.BoxTitle, w_id="ImportTable", max_height=10, 
                name='Importable Tables', scroll_exit=True, )
	
	self.add(GetImportTablesButton, name="Get Importable Tables",)

	self.add(SetImportTableButton, name="Fill in Table to Import", )

	self.add(npyscreen.TitleText, w_id="ImportTableText", name="Table to Import:", begin_entry_at=21 )

	self.add(npyscreen.TitleText, w_id="ImportFileText", name="File to Import:", begin_entry_at=21 )

	self.add(npyscreen.Checkbox, w_id="ImportCheckBox", name = "Import As SQL (if not checked then CSV)")

        self.add(GoImportButton, name="Go", )

    def change_to_admin_form(self, *args, **keywords):
	name = "ADMIN"

        self.parentApp.change_form(name)

    def change_to_structure_form(self, *args, **keywords):
	name = "STRUCTURE"

        self.parentApp.change_form(name)

    def change_to_sql_form(self, *args, **keywords):
	name = "SQLENTRY"

        self.parentApp.change_form(name)

    def change_to_browse_form(self, *args, **keywords):
        name = "BROWSE"

        self.parentApp.change_form(name)

    def change_to_import_form(self, *args, **keywords):
	name = "IMPORT"

        self.parentApp.change_form(name)

    def change_to_export_form(self, *args, **keywords):
	name = "EXPORT"

        self.parentApp.change_form(name)

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

############### Export Form Code #######################

class GetExportTablesButton(npyscreen.ButtonPress):
    def whenPressed(self):
        global con
        cur = con.cursor()
        cur.execute("""SELECT table_name From information_schema.tables WHERE table_schema = 'public'""")
        rows = cur.fetchall()
        outputList = []

        for row in rows:
            #parse out the table name only

	    temp=str(row)
	    temp2 = temp.split("'")
	    temp3 = temp2[1]

	    outputList.append(temp3)

        self.parent.get_widget('ExportTable').values = outputList
        self.parent.get_widget('ExportTable').display()

	return

class SetExportTableButton(npyscreen.ButtonPress):
    def whenPressed(self):
        selectedLineNumber = self.parent.get_widget('ExportTable').value

	if (selectedLineNumber==None):
	   return;

        outputText = self.parent.get_widget('ExportTable').values[selectedLineNumber]

        self.parent.get_widget('ExportTableText').value = outputText
        self.parent.get_widget('ExportTableText').display()

	return

class GoExportButton(npyscreen.ButtonPress):
    def whenPressed(self):
        try:
	    # get the user input fields

	    tableName = self.parent.get_widget('ExportTableText').value
	    fileName = self.parent.get_widget('ExportFileText').value

	    if (tableName==""):
		return

	    if (fileName==""):
		return

            # declare the global con

            global con

	    # from import

            sql = "select * from " + tableName + ";"

	    # read the sql query

	    df = read_sql(sql, con, coerce_float=True, params=None)

	    # write to file

	    fileCheck = self.parent.get_widget('ExportCheckBox').value

	    if(fileCheck==1):
    		if os.path.exists(fileName):
        		os.remove(fileName)
		sql_db = sqlite3.connect(fileName)
		df.to_sql(name=tableName, con=sql_db)
    		sql_db.close()
	    else:
		df.to_csv(fileName,mode='w')

	    outputText = "Database table: " + tableName + " Written to file: " + fileName
		
	    npyscreen.notify_confirm(outputText)
	       
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")

            return

class ExportForm(npyscreen.ActionForm):
    def create(self):
        self.show_atx=22
        self.show_aty=3

	self.add(npyscreen.BoxTitle, w_id="ExportTable", 
		 max_height=10, name='Exportable Tables', scroll_exit=True, )
	
	self.add(GetExportTablesButton, name="Get Exportable Tables" )

	self.add(SetExportTableButton, name="Fill in Table to Export" )

	self.add(npyscreen.TitleText, w_id="ExportTableText", name="Table to Export:", begin_entry_at=21 )

	self.add(npyscreen.TitleText, w_id="ExportFileText", name="File to Export:", begin_entry_at=21 )

	self.add(npyscreen.Checkbox, w_id="ExportCheckBox", name = "Export As SQL (if not checked then CSV)")

        self.add(GoExportButton, name="Go")

    def change_to_admin_form(self, *args, **keywords):
	name = "ADMIN"

        self.parentApp.change_form(name)

    def change_to_structure_form(self, *args, **keywords):
	name = "STRUCTURE"

        self.parentApp.change_form(name)

    def change_to_sql_form(self, *args, **keywords):
	name = "SQLENTRY"

        self.parentApp.change_form(name)

    def change_to_browse_form(self, *args, **keywords):
        name = "BROWSE"

        self.parentApp.change_form(name)

    def change_to_import_form(self, *args, **keywords):
	name = "IMPORT"

        self.parentApp.change_form(name)

    def change_to_export_form(self, *args, **keywords):
	name = "EXPORT"

        self.parentApp.change_form(name)

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

########## Browse Database #########

class BrowseDatabase(npyscreen.ActionForm):
    def create(self):
        self.show_atx=22
        self.show_aty=3
        self.add(ShowTablesButton, name="Select Tables to Browse")
        self.add(npyscreen.TitleSelectOne, w_id="BrowseMenu", name="Table List:", max_height=7, scroll_exit=True, )
        self.add(BrowseSelectedTableButton, name="Browse Selected Table")
        self.add(npyscreen.BoxTitle, w_id="TableData", name="Table Data:", max_height=7, scroll_exit=True)

    def change_to_browse_form(self, *args, **keywords):
        name = "BROWSE"
        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

class ShowTablesButton(npyscreen.ButtonPress):
    def whenPressed(self):
        try:
            global con
            cur = con.cursor()
            cur.execute("""SELECT table_name From information_schema.tables WHERE table_schema = 'public'""")
            rows = cur.fetchall()
            outputList = []
            for row in rows:
                outputList.append(row)
            self.parent.get_widget('BrowseMenu').values = [val[0] for val in outputList]
            self.parent.get_widget('BrowseMenu').display()
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")
        return

class BrowseSelectedTableButton(npyscreen.ButtonPress):
    def whenPressed(self):
        selection = self.parent.get_widget('BrowseMenu').get_selected_objects()

        try:
            global con
            cur = con.cursor()
            cur.execute("SELECT * From " + str(selection[0]))
            col_names = [cn[0] for cn in cur.description]
            rows = cur.fetchall()
            outputList = []
            outputList.append(col_names)
            for row in rows:
                outputList.append(str(row))
            self.parent.get_widget('TableData').values = outputList
            self.parent.get_widget('TableData').display()

        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")
        return

########## ADMIN #########

class AddDatabaseButton(npyscreen.ButtonPress):
    def whenPressed(self):
        addDatabaseName = self.parent.get_widget('DbNameText').get_value()

        try:
            global adminCon
	    adminCon.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = adminCon.cursor()
	    command = "CREATE DATABASE " + addDatabaseName + ";";
            cur.execute(command)
	    npyscreen.notify_confirm("Database name: " + addDatabaseName + " Created!")
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if adminCon:
                adminCon.rollback()

            npyscreen.notify_confirm(" Command did not work!  Please try again!")

	return

class DeleteDatabaseButton(npyscreen.ButtonPress):
    def whenPressed(self):
        deleteDatabaseName = self.parent.get_widget('DbNameText').get_value()

        try:
            global adminCon

            cur = adminCon.cursor()
	    adminCon.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
	    command = "DROP DATABASE " + deleteDatabaseName + ";";
            cur.execute(command)

	    npyscreen.notify_confirm("Database name: " + deleteDatabaseName + " Deleted!")
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if adminCon:
                adminCon.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")

	return

class AdminForm(npyscreen.ActionForm):
    def create(self):
        self.show_atx=22
        self.show_aty=3

	self.add(npyscreen.TitleText, w_id="DbNameText", name="Database Name:", begin_entry_at=21)
	self.add(AddDatabaseButton, name="Add Database" )
	self.add(DeleteDatabaseButton, name="Delete Database" )

    def change_to_admin_form(self, *args, **keywords):
        name = "ADMIN"
        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

####SEARCH####
class SearchCommandButton(npyscreen.ButtonPress):
    def whenPressed(self):
	selectedTable = self.parent.get_widget('SearchMenu').get_selected_objects()
	checkedOrder=self.parent.get_widget('SearchCheckBox').value
	
	try:
            # declare the global con

            global con

            # get current database connection

            cur = con.cursor()

            # execute it
            if(checkedOrder==1):
                cur.execute("SELECT * FROM " + str(selectedTable[0]) + " ORDER BY name ASC")

	    else:
		cur.execute("SELECT * FROM " + str(selectedTable[0]) + " ORDER BY name DESC")

            rows = cur.fetchall()

       	    outputList = []

                # convert the row objects returned into individual strings
            
           
            outputList.append("-----------------------------------------------------")
       	    for row in rows:
		outputList.append(str(row))
                outputList.append("----------------------------------------------------- ")

                # add strings to the ResultTextBox
            self.parent.get_widget('ResultTextBox').values = outputList

                # now display the values that were added

            self.parent.get_widget('ResultTextBox').display()
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")

            return


class SearchEntryForm(npyscreen.ActionForm):
    def create(self):

	# self.add(AdminButton, name="Admin", relx=1, rely=1)
	# self.add(StructureButton, name="Structure", relx=9, rely=1)
	# self.add(SqlButton, name="SQL", relx=21, rely=1)	
	# self.add(QueryButton, name="Query", relx=28, rely=1)
	# self.add(BrowseButton, name="Browse", relx=36, rely=1)
	# self.add(SearchButton, name="Search", relx=45, rely=1)
	# self.add(ExportButton, name="Export", relx=55, rely=1)
	# self.add(ImportButton, name="Import", relx=65, rely=1)

	self.show_atx = 22
	self.show_aty = 3

	
	
        self.add(SearchAllButton, name="Select Table to Search")
        self.add(npyscreen.TitleSelectOne, w_id="SearchMenu", name="Table List:", max_height=5, scroll_exit=True, )
	self.add(npyscreen.Checkbox, w_id="SearchCheckBox", name = "Order by Ascending (if not checked then Descending)")
	self.add(SearchCommandButton, name="Select Table")
	



        self.add(npyscreen.BoxTitle, w_id="ResultTextBox", name="Result of Search:", max_height=7,
				   max_width =50,
                                   scroll_exit=True,
                                   contained_widget_arguments={
                                       'color': "WARNING",
                                       'widgets_inherit_color': True, },
                                   )


	#self.dbNumber = self.add(npyscreen.TitleText, name='#')
        #self.varName = self.add(npyscreen.TitleText, name='Name')
        #self.varType = self.add(npyscreen.TitleText, name='Type')
	#self.collation = self.add(npyscreen.TitleText, name='Collation')
        #self.attributes = self.add(npyscreen.TitleText, name='Attributes')
        #self.null = self.add(npyscreen.TitleText, name='Null')
	#self.default = self.add(npyscreen.TitleText, name='Default')
        #self.extra = self.add(npyscreen.TitleText, name='Extra')

    def change_to_search_form(self, *args, **keywords):
	name = "SEARCH"

        self.parentApp.change_form(name)

    def on_ok(self):
        self.parentApp.switchForm("EMPTY")

class SearchAllButton(npyscreen.ButtonPress):
    def whenPressed(self):
        try:
            global con
            cur = con.cursor()
            cur.execute("""SELECT table_name From information_schema.tables WHERE table_schema = 'public'""")
            rows = cur.fetchall()
            outputList = []
            for row in rows:
                outputList.append(row)
            self.parent.get_widget('SearchMenu').values = [val[0] for val in outputList]
            self.parent.get_widget('SearchMenu').display()
        except psycopg2.DatabaseError, e:
            # clear the current transaction to free up the con

            if con:
                con.rollback()

            npyscreen.notify_confirm("Command did not work!  Please try again!")
        return



########## MAIN CLASS #########

class SqlEntryApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="Connect to Database", color="WARNING", )
	self.addForm("EMPTY", EmptyForm, name="NCURSES Admin", color="GREEN", )
	self.addForm("ADMIN", AdminForm, name="Administration", color="IMPORTANT", lines=20, columns=55 )
        self.addForm("SQLENTRY", SqlEntryForm, name="SQL Command Tool", color="IMPORTANT", lines=20, columns=55 )
        self.addForm("BROWSE", BrowseDatabase, name="Browse Database", color="IMORTANT", lines=20, columns=55 )
	self.addForm("STRUCTURE", StructureEntryForm, name="Structure Tool", color="IMPORTANT", lines=20, columns=55 )
	self.addForm("SEARCH", SearchEntryForm, name="Search Tool", color="IMPORTANT", lines=20, columns=55 )
	self.addForm("IMPORT", ImportForm, name="Import", color="GREEN", lines=20, columns=55 )
	self.addForm("EXPORT", ExportForm, name="Export", color="GREEN",lines=20, columns=55 )

    def onCleanExit(self):
        if con:
            con.close()

    def change_form(self, name):
        self.switchForm(name)
        self.resetHistory()


########## MAIN PROGRAM #########

def main():
    SEA = SqlEntryApp()
    SEA.run()


if __name__ == "__main__":
    main()
