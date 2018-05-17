/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   paper-dialog.html
 */

/// <reference path="../polymer/types/polymer.d.ts" />
/// <reference path="../neon-animation/neon-animation-runner-behavior.d.ts" />
/// <reference path="../paper-dialog-behavior/paper-dialog-behavior.d.ts" />
/// <reference path="../paper-dialog-behavior/paper-dialog-shared-styles.d.ts" />

/**
 * Material design: [Dialogs](https://www.google.com/design/spec/components/dialogs.html)
 *
 * `<paper-dialog>` is a dialog with Material Design styling and optional animations when it is
 * opened or closed. It provides styles for a header, content area, and an action area for buttons.
 * You can use the `<paper-dialog-scrollable>` element (in its own repository) if you need a scrolling
 * content area. To autofocus a specific child element after opening the dialog, give it the `autofocus`
 * attribute. See `Polymer.PaperDialogBehavior` and `Polymer.IronOverlayBehavior` for specifics.
 *
 * For example, the following code implements a dialog with a header, scrolling content area and
 * buttons. Focus will be given to the `dialog-confirm` button when the dialog is opened.
 *
 *     <paper-dialog>
 *       <h2>Header</h2>
 *       <paper-dialog-scrollable>
 *         Lorem ipsum...
 *       </paper-dialog-scrollable>
 *       <div class="buttons">
 *         <paper-button dialog-dismiss>Cancel</paper-button>
 *         <paper-button dialog-confirm autofocus>Accept</paper-button>
 *       </div>
 *     </paper-dialog>
 *
 * ### Styling
 *
 * See the docs for `Polymer.PaperDialogBehavior` for the custom properties available for styling
 * this element.
 *
 * ### Animations
 *
 * Set the `entry-animation` and/or `exit-animation` attributes to add an animation when the dialog
 * is opened or closed. See the documentation in
 * [PolymerElements/neon-animation](https://github.com/PolymerElements/neon-animation) for more info.
 *
 * For example:
 *
 *     <link rel="import" href="components/neon-animation/animations/scale-up-animation.html">
 *     <link rel="import" href="components/neon-animation/animations/fade-out-animation.html">
 *
 *     <paper-dialog entry-animation="scale-up-animation"
 *                   exit-animation="fade-out-animation">
 *       <h2>Header</h2>
 *       <div>Dialog body</div>
 *     </paper-dialog>
 *
 * ### Accessibility
 *
 * See the docs for `Polymer.PaperDialogBehavior` for accessibility features implemented by this
 * element.
 */
interface PaperDialogElement extends Polymer.Element, Polymer.PaperDialogBehavior, Polymer.NeonAnimationRunnerBehavior {
  _renderOpened(): void;
  _renderClosed(): void;
  _onNeonAnimationFinish(): void;
}

interface HTMLElementTagNameMap {
  "paper-dialog": PaperDialogElement;
}
