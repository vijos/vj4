# VJ4 Web Icons

VJ4 uses [IcoMoon](https://icomoon.io) to manage and generate webfont for icons.

## Getting Started

1. Open [IcoMoon App](https://icomoon.io/app/#/projects) using a modern browser.

2. Click `Import Project` and select `vj4/ui/misc/fonts/.icomoon_selection.json`.

   > For OS X users: you may want to show hidden files in the open dialog by pressing `Command` + `Shift` + `.` in order to choose `.icomoon_selection.json`.

3. The new project will appear as `Untitled Project 1`. Rename it to `vj4` if you wish.

4. Click `Load`

IcoMoon will memorize the project at local. You needn't repeat this step the next time you use IcoMoon App. However you do need to re-import icons if others have updated icons in repository.

## Manage Icons

See IcoMoon manual.

## Export Webfont

1. Click `Generate Font` at the footer bar in App.

2. Click `Download` button.

3. You will get `icomoon.zip`, extract it.

4. Open terminal and `cd` into your extracted directory (which contains `style.css`, `selection.json` and so on)

5. Execute `$PROJECT_ROOT/scripts/copy_icomoon_fonts.sh`, in which `$PROJECT_ROOT` is the location of VJ4.

TADA! Now you can use your icon by writing `<i class="..."></i>`. Click `Get Code` in the `Generate Font` page to know the HTML of your icon.