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
