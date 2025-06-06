# TOML Init
This is a simple library to handle default config creation and validation on start.

I made this as I install my projects on various machines and enviroments, and I found myself doing this process a lot, especially when using many modules. 

## Info
`Config Folder Path` = "/configs"
`Default Config Folder Path` = "/configs/defaults"
`Default Master Config File Name` = "config.toml"

## Useage
If the `Config Folder Path` and `Default Config Folder Path` do not exist, it will create them and then exit.
It will look for a file in `Config Folder Path` named *.toml it doesn't care about the file name, only the extension.
 - If multiple files with a .toml extension exist, it will error out.
 - If a valid file doesn't exist if will create one named in accordance with `Default Master Config File Name`.

If there are .toml files in `Default Config Folder Path` if will loop over them.

## Default File Format
```
[info]
block_name = 

[items]
<item name> = <default value>
<item name> = {"defaultValue" = <default value>,  "type" = <item type>, "min" = <minimum value>, "max' = <maximum value>}
```

## Syntax
With the exception of `<default value>` the other parameters are optional. If you don't intend to use them, you can use the simple declaration `<item name> = <default value>`

## Example
```
[info]
block_name = file.saver

[items]
SHOW_TRAY_TIPS      = False
WINDOW_LOAD_DELAY   = {"defaultValue" = 0.5,  "type" = "float", "min" = 0.0}
NAVIGATION_DELAY    = {"defaultValue" = 0.15, "type" = "float", "min" = 0.0}
QUICKBOOKS_NAME     = {"defaultValue" = "Intuit QuickBooks Enterprise Solutions", "type" = "str"}
```


## Current Features
| Feature             | Description                                                                                        |
|---------------------|----------------------------------------------------------------------------------------------------|
| Single config files | Will take individual default config files and validate and combine them into a single config file. |
| Default value       | The default value for that item, will be used if non existent or invalid                           |
| Value type          | The expected value type, will trigger a reset if not passed.                                       |
| Min                 | The minimum accepted value.                                                                        |
| Max                 | The maximum accepted value.                                                                        |


## Potential Future Features
| Feature                     | Description                                                          |
|-----------------------------|----------------------------------------------------------------------|
| Multiple config files       | Will support having separate config files for organization purposes? |
| Comment injection           | Allow comments to be specified in the defaults?                      |
| Changing directory defaults | Allow the directory defaults to be changed?                          |
