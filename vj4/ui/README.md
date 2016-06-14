# Vijos UI Language

## Layout

### Content Container

By using a content container, you can adapt contents to a standard width for different browser window sizes. The container itself is always horizontally center-aligned to the parent. Nested content containers are not supported.

| Window Width | Container Width | Size Description |
|--------------|-----------------|------------------|
| >= 1250px    | 1200px          | Desktop HD       |
| >= 1000px    | 980px           | Desktop          |
| < 1000px     | 100% (*)        | Tablet or Mobile |

\* The container contains 20px padding horizontally.

```html
<div class="content-container">
  Content here
</div>
```

### Auto-Expand Container

The auto-expand container can expand the height of one of its children (marked as `autoexpand__expand`) so that the height of the whole container is always equal to or larger than the height of the browser window.

```html
<div class="autoexpand__container">
  <div class="autoexpand__collapse">
    Header
  </div>
  <div class="autoexpand__expand">
    The height of this element will be expanded to fill
    the extra space of the window.
  </div>
  <div class="autoexpand__collapse">
    Footer
  </div>
</div>
```

### Two-Column

The most-commonly-used two-column layout (aka sidebar) is supported natively. The layout is responsive, which is, for desktop (width >= 1000px), the sidebar and the main content is arranged horizontally and the sidebar always occupies 75% width of the parent container. For tablet or mobile (width < 1000px), they are arranged vertically and they both occupy 100% width of the parent container.

Sidebar at right (in desktop) / below the main content (in non-desktop):

```html
<div class="layout--2col clearfix">
  <div class="layout--2col__main">
    Main
  </div>
  <div class="layout--2col__side">
    Right Sidebar
  </div>
</div>
```

Sidebar at left (in desktop) / above the main content (in non-desktop):

```html
<div class="layout--2col clearfix">
  <div class="layout--2col__side">
    Left Sidebar
  </div>
  <div class="layout--2col__main">
    Main
  </div>
</div>
```

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

```html
<div class="section">
  Section content
</div>
```

#### Indent

Because some section elements (for example, table) should occupy all horizontal space, the section element itself doesn't contain spacings.

If you want to add spacings for contents, you can wrap contents with `<div class="section__indent"></div>`. It must be used along with class name `left`, `right`, `top`, `bottom`.

```html
<div class="section">
  <div class="section__indent top">
    top padding
  </div>
  <div class="section__indent left right">
    left and right padding
  </div>
  <div class="section__indent bottom">
    bottom padding
  </div>
</div>
```

Notice that the spacing of adjacent `section__indent` element will be collapsed. See [margin collapsing](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Box_Model/Mastering_margin_collapsing) for details.

#### Title

You can use `<X class="section__title"></X>` to specify the title for a section (`X` is `h1` to `h3`). The font size and the color of the section title is different from normal headings.

The section title itself contains left and right paddings and the amount is exactly the same as `section__indent`, which means that the section title should not be put inside a horizontal-padding container (`section__indent left right`).

```html
<div class="section">
  <div class="section__indent top bottom">
    <h1 class="section__title">Section title</h1>
  </div>
</div>
```

#### Table

If the main content of the section is a data table (or additionally with a title and a paginator), it is suggested to apply `section__table` to the table. Section table should not be put inside a horizontal-padding container as well.

2 * 3 table sample:

```html
<div class="section">
  <div class="section__indent top bottom">
    <table class="section__table">
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
  <div class="section__indent top bottom left right">
    Section content
  </div>
</div>
```

Section with title and content:

```html
<div class="section">
  <div class="section__indent top bottom">
    <h1 class="section__title">Section title</h1>
    <div class="section__indent left right">
      Section content
    </div>
  </div>
</div>
```

Section with title and table content:

```html
<div class="section">
  <div class="section__indent top bottom">
    <h1 class="section__title">Section title</h1>
    <table class="section__table">
      ...
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

`expanded`: The input would occupy full width of the parent.

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

### Text Alignment

```html
<ANY class="text-center"></ANY>
<ANY class="text-right"></ANY>
```

