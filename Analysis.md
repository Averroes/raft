# Introduction to Analysis #

After getting your data into RAFT's request/response store, use an analyzer to convert data into meaningful information.  RAFT provides useful built-in analyzers, and provides a simple, yet powerful way for you to write your own analyzers for the task at hand.

The rest of this page discusses using analyzers in RAFT.  To learn more about writing your own analyzers, see [AnalyzerDevelopment](AnalyzerDevelopment.md).

## Using an existing analyzer ##
Analysis consists of three steps:
  1. Choose and configure the analyzers to use (optional)
  1. Run the analysis
  1. View the results

### Configuration ###
Use the "Configuration -> Analysis Configuration" menu to open the configuration dialog.

PIC

The configuration dialog shows a list of available analyzers on the left hand side.  Each can be enabled or disabled with the checkboxes shown.  Click the "Save All" button to save your changes to enabled/disabled state.

PIC

When an analyzer is selected, the bottom pane shows detailed information about the analyzer selected.  The right hand pane shows any configuration options for the analyzer.  Both the keys and values can be edited (see the analyzer information for details about what each analyzer's configuration settings do).  To remove an item from the configuration tree, select the item and click the "-" button.  To add an item, first select a node in the tree to use as a base, then click the "+" button.  A new node will be created at the same level with a similar name.

  * **IMPORTANT:** After setting analysis configuration, click "Save" before selecting a new analyzer or your changes will be lost.  This will be fixed in a future version of RAFT.

### Run Analysis ###
To run analysis, select the "Start Analysis" button from the action toolbar.

PIC

A status bar dialog will appear.  When the dialog closes, analysis is complete.  Analysis time will depend on the quantity of data analyzed and the number of analyzers run on the content.  The results are saved to the RAFT database and are available for viewing on the analysis tab.

### View Analysis Results ###
Click on the "Analysis" tab to view the results of past analysis.  Each analysis session is displayed, sorted by date.  To view analysis data, drill down on an analysis session.  Details will be shown in the right hand pane.

PIC

When a selected analysis result is specific to a particular request/response, the relevant request/response will be shown in the request response pane at the bottom right.