/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   paper-tooltip.html
 */

/// <reference path="../polymer/types/polymer.d.ts" />

/**
 * Material design: [Tooltips](https://www.google.com/design/spec/components/tooltips.html)
 * `<paper-tooltip>` is a label that appears on hover and focus when the user
 * hovers over an element with the cursor or with the keyboard. It will be centered
 * to an anchor element specified in the `for` attribute, or, if that doesn't exist,
 * centered to the parent node containing it. Note that as of `paper-tooltip#2.0.0`,
 * you must explicitely include the `web-animations` polyfill if you want this
 * element to work on browsers not implementing the WebAnimations spec.
 * Example:
 *     // polyfill
 *     <link rel="import" href="../../neon-animation/web-animations.html">
 *     <div style="display:inline-block">
 *       <button>Click me!</button>
 *       <paper-tooltip>Tooltip text</paper-tooltip>
 *     </div>
 *     <div>
 *       <button id="btn">Click me!</button>
 *       <paper-tooltip for="btn">Tooltip text</paper-tooltip>
 *     </div>
 * The tooltip can be positioned on the top|bottom|left|right of the anchor using
 * the `position` attribute. The default position is bottom.
 *     <paper-tooltip for="btn" position="left">Tooltip text</paper-tooltip>
 *     <paper-tooltip for="btn" position="top">Tooltip text</paper-tooltip>
 * ### Styling
 * The following custom properties and mixins are available for styling:
 * Custom property | Description | Default
 * ----------------|-------------|----------
 * `--paper-tooltip-background` | The background color of the tooltip | `#616161`
 * `--paper-tooltip-opacity` | The opacity of the tooltip | `0.9`
 * `--paper-tooltip-text-color` | The text color of the tooltip | `white`
 * `--paper-tooltip` | Mixin applied to the tooltip | `{}`
 * `--paper-tooltip-delay-in` | Delay before tooltip starts to fade in | `500`
 * `--paper-tooltip-delay-out` | Delay before tooltip starts to fade out | `0`
 * `--paper-tooltip-duration-in` | Timing for Animation when showing tooltip | `500`
 * `--paper-tooltip-duration-out` | Timining for Animation when hiding tooltip | `0`
 * `--paper-tooltip-animation` | Mixin applied to the tooltip animation | `{}`
 */
interface PaperTooltipElement extends Polymer.Element {

  /**
   * The id of the element that the tooltip is anchored to. This element
   * must be a sibling of the tooltip. If this property is not set,
   * then the tooltip will be centered to the parent node containing it.
   */
  for: string|null|undefined;

  /**
   * Set this to true if you want to manually control when the tooltip
   * is shown or hidden.
   */
  manualMode: boolean|null|undefined;

  /**
   * Positions the tooltip to the top, right, bottom, left of its content.
   */
  position: string|null|undefined;

  /**
   * If true, no parts of the tooltip will ever be shown offscreen.
   */
  fitToVisibleBounds: boolean|null|undefined;

  /**
   * The spacing between the top of the tooltip and the element it is
   * anchored to.
   */
  offset: number|null|undefined;

  /**
   * This property is deprecated, but left over so that it doesn't
   * break exiting code. Please use `offset` instead. If both `offset` and
   * `marginTop` are provided, `marginTop` will be ignored.
   */
  marginTop: number|null|undefined;

  /**
   * The delay that will be applied before the `entry` animation is
   * played when showing the tooltip.
   */
  animationDelay: number|null|undefined;

  /**
   * The animation that will be played on entry.  This replaces the
   * deprecated animationConfig.  Entries here will override the
   * animationConfig settings.  You can enter your own animation
   * by setting it to the css class name.
   */
  animationEntry: string|null|undefined;

  /**
   * The animation that will be played on exit.  This replaces the
   * deprecated animationConfig.  Entries here will override the
   * animationConfig settings.  You can enter your own animation
   * by setting it to the css class name.
   */
  animationExit: string|null|undefined;

  /**
   * This property is deprecated.  Use --paper-tooltip-animation to change the animation.
   * The entry and exit animations that will be played when showing and
   * hiding the tooltip. If you want to override this, you must ensure
   * that your animationConfig has the exact format below.
   */
  animationConfig: object|null|undefined;
  _showing: boolean|null|undefined;
  hostAttributes: object|null;

  /**
   * Returns the target element that this tooltip is anchored to. It is
   * either the element given by the `for` attribute, or the immediate parent
   * of the tooltip.
   */
  readonly target: any;
  attached(): void;
  detached(): void;

  /**
   * Replaces Neon-Animation playAnimation - just calls show and hide.
   *
   * @param type Either `entry` or `exit`
   */
  playAnimation(type: string): void;

  /**
   * Cancels the animation and either fully shows or fully hides tooltip
   */
  cancelAnimation(): void;

  /**
   * Shows the tooltip programatically
   */
  show(): void;

  /**
   * Hides the tooltip programatically
   */
  hide(): void;
  updatePosition(): void;
  _addListeners(): void;
  _findTarget(): void;
  _delayChange(newValue: any): void;
  _manualModeChanged(): void;
  _cancelAnimation(): void;
  _onAnimationFinish(): void;
  _onAnimationEnd(): void;
  _getAnimationType(type: any): any;
  _removeListeners(): void;
}

interface HTMLElementTagNameMap {
  "paper-tooltip": PaperTooltipElement;
}
