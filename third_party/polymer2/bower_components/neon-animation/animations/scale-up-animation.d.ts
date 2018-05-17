/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   animations/scale-up-animation.html
 */

/// <reference path="../../polymer/types/polymer.d.ts" />
/// <reference path="../neon-animation-behavior.d.ts" />

/**
 * `<scale-up-animation>` animates the scale transform of an element from 0 to 1. By default it
 * scales in both the x and y axes.
 *
 * Configuration:
 * ```
 * {
 *   name: 'scale-up-animation',
 *   node: <node>,
 *   axis: 'x' | 'y' | '',
 *   transformOrigin: <transform-origin>,
 *   timing: <animation-timing>
 * }
 * ```
 */
interface ScaleUpAnimationElement extends Polymer.Element, Polymer.NeonAnimationBehavior {
  configure(config: any): any;
}

interface HTMLElementTagNameMap {
  "scale-up-animation": ScaleUpAnimationElement;
}
