# utils
Useful utils and scripts, mostly python



# go_header


Takes GO func declaration from the clipboard and makes nice header with arguments and return values. Places this description into clipboard

```
command line args:
-s:<path>               -   path to recursively scan *.go files for existing descriptions
-o:<type>=<value>       -   add an output value type/description pair, example:  "-o:[]byte=raw JSON response."



Working example:

"  func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {"

will be processed like this:

// GetTransactionsPage()
// --> Input:
// context     *zaboutils.ExtendedContext     .
// account     *zaboresources.Account         .
// cursor      *string                        .
// <-- Output:
// 1) []*zaboresources.AccountTransactionRes     .
// 2) *string                                    .
// 3) bool                                       .
// 4) *echo.HTTPError                            .


```



# func_name 



Goes though all go files in the tree and looks for inconsistent usage of zaboutils.FuncName : - argument of it must be
the same as the surrounding func name 

command line args:
-s:<path>               -   path to recursively scan *.go files 



Working example:
```
func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {

...
	c.logger.LogWithContextf(zaboutils.Severity.INFO, context, zaboutils.FuncName(c.GetBalance), "Next cursor is %v", sMarker)
...
}
```

-- this should issue a warning as GetTransactionsPage != GetBalance


# cross_names


Goes though all go files in the tree and looks for copy-paste dirt : 
command line args:
-s:<path>               -   path to recursively scan *.go files 



Working example:

in the zabo-api-provider-gemini/
(and assuming there is a folder zabo-api-provider-bittrex/ 
```
func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {
...
	c.logger.LogWithContextf(zaboutils.Severity.INFO, context, zaboutils.FuncName(c.GetBalance), "Next cursor is %v", "Bittrex")
...
}
```
-- this should issue a warning as the word bittrex is out of context



# zabo logs


zabo_logs retrieves all log entries for a request id

usage:
```
python zabo_logs.py [-r] [-s:<severity level>]  <request id>

-r reverses log entries to the natural order (older first)
-s:<int>  minimal severity level: 1 - all including DEBUG(default), 2 - INFO and higher, 3 - WARNING and ERROR, 4 - ERROR and CRITICALs  
```
Example:
```
python zabo_logs.py -r -s:2  63052069-a61d-4bda-b756-2f6c81367607  > "63052069-a61d-4bda-b756-2f6c81367607.log"
```

it uses login/password and those are need to be placed in a file ~/.config/zabo_credentials:

sample contents, two lines of text:
```
myusername
mypassword
``` 


access token will be saved in "/tmp/zabo_bearer.txt"
you can change this location in the global section below (if you feel it's not secure)
