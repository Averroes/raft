# Analyzer Basics #

The fastest way to develop a new analyzer is to make a copy of `raft/analysis/analyzers/SampleTemplate.py`, then make modifications.

The file itself is well documented, and is shown below with some extra tips.  To help understand the flow of analysis at execution time, you can uncomment the print statements and run RAFT from the command line to see the flow.

```

from ..AbstractAnalyzer import AbstractAnalyzer


class SampleTemplateClassName(AbstractAnalyzer):
```
Change the `SampleTemplateClassName` to whatever you'd like, but don't change the rest of this part until you understand the system a little more.

```
    def __init__(self):
        self.desc="SampleTemplate Description."
        self.friendlyname="Sample Template Friendly Name"
```
The description and friendlyname are displayed on the configuration dialog and in the analysis results.  Friendlyname should be fairly short (a few words), but desc can be as long as needed.  The description can include HTML formatting, but be sure to properly close any tags you open.

```
    def preanalysis(self):
        #print "preanalysis: This function runs once at the start of analysis."
        #print "Delete this function if you don't have any preanalysis setup."
        pass
```
Any special setup for your analyzer happens here.  For example, if you have a special datastore you need to persist between each page analysis, set it up here.

Many analyzers will not need this function at all (it can be safely deleted).

```
    def analyzeTransaction(self, target, results):
        #print "-------------------------------------------------------------------------------"
        #print "analyzeTransaction():"
        #print "This function gets run once per request/response pair to be analyzed."
        #print "We are now analyzing %s:%s"%(target.responseId,target.responseUrl)
        #print "You must define this function."
        #print "-------------------------------------------------------------------------------"
```
This is where you will put the analysis logic that runs on each page.  RAFT officially only supports passive analysis on the request/response `target` object, but in theory you can actually do whatever you want.

For more information about the `target` object, see http://code.google.com/p/raft/source/browse/trunk/core/RequestResponse.py
```
        #To  add a finding, call this (note the slight difference between this and the addOverallResult call below):
        results.addPageResult(pageid=target.responseId,
                                 url=target.responseUrl,
                                 type='Short Finding Name',
                                 desc='A longer description of the problemAlso, here are your config values: %s'%self.getCurrentConfiguration(),
                                 data={'somekey1':'somevalue1',
                                           'somekey2':1337},  #any base python type (list, dict, int, bool, str) works here
                                 span=(1337,31137), #This is the first character and last character where the finding was detected.
                                                                 #None is ok here too if it's not pinpointable.
                                 severity='SAMPLE: NOT A FINDING',  #High, Medium, Low, or make your own
                                 certainty='HIGH' #High, Medium, Low, or make your own
                                 )

```

Once you've done any logic on a given request/response and decided to report something, this is how you declare a finding.  The finding will be automatically saved to the database and displayed on the analysis tab.

There's nothing that says that a single analyzeTransaction() call can't have multiple results.  For example, if you're searching for credit card numbers on a page, you might want to have a result for each credit card number found.

```
        
        
    def postanalysis(self,results):
        #print "This function runs once after all request/response pairs were analyzed."
        #print "Define if it you need some sort of 'overall' analysis after your per-page analysis."
        #print "Delete it if you don't do that."
        #To  add a finding, call this (note the slight difference between this and the addPageResult call above):
        results.addOverallResult(
                                context="*.example.com",
                                type='Short Finding Name',
                                desc='A longer description of the problem.  Also, here are your config values: %s'%self.getCurrentConfiguration(),
                                data={'somekey1':'somevalue1',
                                               'somekey2':1337},  #any base python type (list, dict, int, bool, str) works here
                                span=None ,               #This is the first character and last character where the finding was detected.
                                                                 #None is ok here too if it's not pinpointable.
                                severity='SAMPLE: NOT A FINDING',  #High, Medium, Low, or make your own
                                certainty='HIGH' #High, Medium, Low, or make your own
                                    )
```

Similar to the `addPageResult` method above, this is where you put any logic to decide if there's something to report, and generate the result object.

The difference is that this function is run only once, after all requests/responses were analyzed.  If you have "overall" results that applies to a broad context instead of a single page, you can note them here.

```
    def getDefaultConfiguration(self):
        #Any config values are defined here.  Users can change them in the Analysis Config section
        #To access the values, use self.getCurrentConfiguration(), which will return the dictionary with any
        #modifications made by the user in AnalysisConfig
        return {"Sample Configuration Key":"Sample Configuration Value"}
```

If you have any user configurable values in your analyzer, set their default values here.  This can be a nested dictionary, but leaf node values need to be strings.