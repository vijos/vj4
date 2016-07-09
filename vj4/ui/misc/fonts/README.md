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

TADA! Now you can use your icon by writing `<span class="icon icon-name"></span>`. Click `Get Code` in the `Generate Font` page to know the HTML of your icon.

## Font Properties

- Metrics width = 1024
- Ascent = 960
- Descent = 64
- Em size = 1024

## Codepoint Map

- `0xe200 bold`
- `0xe201 italic`
- `0xe202 quote`
- `0xe203 insert--link`
- `0xe204 insert--image`
- `0xe205 unordered_list`
- `0xe206 ordered_list`
- `0xe207 preview`
- `0xe208 help`
- `0xe209 formula`
- `0xe220 twitter`
- `0xe221 wechat`
- `0xe222 qq`
- `0xe223 google_plus`
- `0xe224 facebook`
- `0xe225 github`
- `0xe226 linkedin`
- `0xe227 mail`
- `0xe228 link`
- `0xe230 hourglass`
- `0xe231 schedule`
- `0xe232 check`
- `0xe233 close`
- `0xe234 chevron_left`
- `0xe235 chevron_right`
- `0xe236 expand_less`
- `0xe237 expand_more`
- `0xe240 enlarge`
- `0xe241 shrink`
- `0xe242 send`
- `0xe243 statistics`
- `0xe244 bubble--outline`
- `0xe245 bubble`
- `0xe246 wrench`
- `0xe247 edit`
- `0xe248 delete`
- `0xe249 flag`
- `0xe24A reply`
- `0xe24B favourite`
- `0xe24C star--outline`
- `0xe24D star`
- `0xe24E play`
- `0xe24F debug`
- `0xe250 search`
- `0xe251 download`
- `0xe252 upload`
- `0xe253 warning`
- `0xe254 block`
- `0xe255 settings`
- `0xe256 message`
- `0xe257 view_headline`
- `0xe258 view_module`
- `0xe259 view_quilt`
- `0xe25A view_stream`
- `0xe25B view_week`
- `0xe25C global`
- `0xe25D tag`
