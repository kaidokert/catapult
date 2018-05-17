/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   iron-menubar-behavior.html
 */

/// <reference path="../polymer/types/polymer.d.ts" />
/// <reference path="iron-menu-behavior.d.ts" />

declare namespace Polymer {

  /**
   * `Polymer.IronMenubarBehavior` implements accessible menubar behavior.
   */
  interface IronMenubarBehavior extends Polymer.IronMenuBehavior {
    keyBindings: object;
    hostAttributes: object|null;
    readonly _isRTL: any;
    _onUpKey(event: any): void;
    _onDownKey(event: any): void;
    _onKeydown(event: any): void;
    _onLeftKey(event: any): void;
    _onRightKey(event: any): void;
  }

  const IronMenubarBehavior: object;
}
