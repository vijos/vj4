# Vijos UI Language

## Layout

### Grid

See [Foundation Grid](http://foundation.zurb.com/sites/docs/grid.html)

### Float

See [Foundation Float](http://foundation.zurb.com/sites/docs/float-classes.html)

> NOTE: `.float-center` is not implemented.

## Typography

HTML elements such as headings (`h1`, `h2`, ...), lists (`ol`, `ul`, `li`, ...) and tables does not have margins and paddings by default in order to easy the styling of semantic structures. However you may want suitable space between those elements when they are used to present content to users (for example, problem content). In this case, you need to enable the typography styling by wrapping them with `<div class="typo"></div>`:

```html
<div class="typo">
  <h1>Notice</h1>
  <p>The content will be well formatted.</p>
  <ul>
    <li>Item</li>
    <li>Item</li>
    <li>Item</li>
  </ul>
</div>
```

### Text Alignment

```html
<ANY class="text-left"></ANY>
<ANY class="text-center"></ANY>
<ANY class="text-right"></ANY>
<ANY class="text-justify"></ANY>
```

## Prototype Components

### Media Object

TODO

### Number Box Object

TODO

### Balancer Object

TODO

## Basic Components

### Section

Section is served as an entry to more detailed contents. By default, each section has a white background and drop-shadow.

A section should contain a section-header and one or more section-body.

```html
<div class="section">
  <div class="section__header">
    <!-- header -->
  </div>
  <div class="section__body">
    <!-- body -->
  </div>
</div>
```

#### Title

You can use `<X class="section__title"></X>` to specify the title for a section (`X` is from `h1` to `h3`). The font size and the color of the section title is different from normal headings.

```html
<div class="section">
  <div class="section__header">
    <h1 class="section__title">Section title</h1>
  </div>
</div>
```

#### Table

If the main content of the section is a data table (or additionally with a title and a paginator), it is suggested to apply `data-table` to the table. Table should be put inside a section-body with `no-padding` decoration.

3 * 2 table sample:

```html
<div class="section">
  <!-- ... -->
  <div class="section__body no-padding">
    <table class="data-table">
      <colgroup>
        <col class="col--1">
        <col class="col--2">
      </colgroup>
      <thead>
        <tr>
          <th class="col--1"></th>
          <th class="col--2"></th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="col--1">1,1</td><td class="col--2">1,2</td></tr>
        <tr><td class="col--1">2,1</td><td class="col--2">2,2</td></tr>
        <tr><td class="col--1">3,1</td><td class="col--2">3,2</td></tr>
      </tbody>
    </table>
  </div>
</div>
```

> If you want to specify the width of a column, you should add `col--xxx` to the class name list (as shown above) and specify its width in a CSS rule like:
>
> ```css
> .col--1 { width: 120px; }
> ```

#### Samples

Section with content:

```html
<div class="section">
  <div class="section__body">
    Section content
  </div>
</div>
```

Section with title and content:

```html
<div class="section">
  <div class="section__header">
    <h1 class="section__title">Section title</h1>
  </div>
  <div class="section__body">
    Section content
  </div>
</div>
```

Section with title and table content:

```html
<div class="section">
  <div class="section__header">
    <h1 class="section__title">Section title</h1>
  </div>
  <div class="section__body no-padding">
    <table class="data-table">
      <!-- ... -->
    </table>
  </div>
</div>
```

### Button

```html
<ANY class="button"></ANY>
```

Additional class names:

`rounded`: The button would have round corners.

`primary`: The button would have blue background.

`expanded`: The button would occupy full width of the parent.

`inverse`: TODO

### Input

```html
<X class="textbox"></X>
```

`X` could be `input` or `textarea`.

Additional class names:

`material`: TODO

`inverse`: TODO

### Paginator

TODO

### Menu

TODO

### Dropdown

TODO

### Navigation

TODO

### Star

TODO

### Tab

TODO

## High-Level Components

### Comment List

TODO

## Other

### JavaScript-Responsive Visibility

#### Hide if JavaScript is disabled

```html
<ANY class="nojs--hide"></ANY>
```

#### Hide if JavaScript is enabled

```html
<ANY class="hasjs--hide"></ANY>
```
