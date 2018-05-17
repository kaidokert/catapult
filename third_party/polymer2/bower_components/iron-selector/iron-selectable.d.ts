/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   iron-selectable.html
 */

/// <reference path="../polymer/types/polymer.d.ts" />
/// <reference path="iron-selection.d.ts" />

declare namespace Polymer {

  interface IronSelectableBehavior {

    /**
     * If you want to use an attribute value or property of an element for
     * `selected` instead of the index, set this to the name of the attribute
     * or property. Hyphenated values are converted to camel case when used to
     * look up the property of a selectable element. Camel cased values are
     * *not* converted to hyphenated values for attribute lookup. It's
     * recommended that you provide the hyphenated form of the name so that
     * selection works in both cases. (Use `attr-or-property-name` instead of
     * `attrOrPropertyName`.)
     */
    attrForSelected: string|null|undefined;

    /**
     * Gets or sets the selected element. The default is to use the index of the item.
     */
    selected: string|number;

    /**
     * Returns the currently selected item.
     */
    readonly selectedItem: object|null;

    /**
     * The event that fires from items when they are selected. Selectable
     * will listen for this event from items and update the selection state.
     * Set to empty string to listen to no events.
     */
    activateEvent: string|null|undefined;

    /**
     * This is a CSS selector string.  If this is set, only items that match the CSS selector
     * are selectable.
     */
    selectable: string|null|undefined;

    /**
     * The class to set on elements when selected.
     */
    selectedClass: string|null|undefined;

    /**
     * The attribute to set on elements when selected.
     */
    selectedAttribute: string|null|undefined;

    /**
     * Default fallback if the selection based on selected with `attrForSelected`
     * is not found.
     */
    fallbackSelection: string|null|undefined;

    /**
     * The list of items from which a selection can be made.
     */
    readonly items: any[]|null|undefined;

    /**
     * The set of excluded elements where the key is the `localName`
     * of the element that will be ignored from the item list.
     */
    _excludedLocalNames: object|null|undefined;

    /**
     *  UNUSED, FOR API COMPATIBILITY
     */
    readonly _shouldUpdateSelection: any;
    created(): void;
    attached(): void;
    detached(): void;

    /**
     * Returns the index of the given item.
     *
     * @returns Returns the index of the item
     */
    indexOf(item: object|null): any;

    /**
     * Selects the given value.
     *
     * @param value the value to select.
     */
    select(value: string|number): void;

    /**
     * Selects the previous item.
     */
    selectPrevious(): void;

    /**
     * Selects the next item.
     */
    selectNext(): void;

    /**
     * Selects the item at the given index.
     */
    selectIndex(index: any): void;

    /**
     * Force a synchronous update of the `items` property.
     *
     * NOTE: Consider listening for the `iron-items-changed` event to respond to
     * updates to the set of selectable items after updates to the DOM list and
     * selection state have been made.
     *
     * WARNING: If you are using this method, you should probably consider an
     * alternate approach. Synchronously querying for items is potentially
     * slow for many use cases. The `items` property will update asynchronously
     * on its own to reflect selectable items in the DOM.
     */
    forceSynchronousItemUpdate(): void;
    _checkFallback(): void;
    _addListener(eventName: any): void;
    _removeListener(eventName: any): void;
    _activateEventChanged(eventName: any, old: any): void;
    _updateItems(): void;
    _updateAttrForSelected(): void;
    _updateSelected(): void;
    _selectSelected(selected: any): void;
    _filterItem(node: any): any;
    _valueToItem(value: any): any;
    _valueToIndex(value: any): any;
    _indexToValue(index: any): any;
    _valueForItem(item: any): any;
    _applySelection(item: any, isSelected: any): void;
    _selectionChange(): void;

    /**
     * observe items change under the given node.
     */
    _observeItems(node: any): any;
    _activateHandler(e: any): void;
    _itemActivate(value: any, item: any): void;
  }

  const IronSelectableBehavior: object;
}
