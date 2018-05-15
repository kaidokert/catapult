/**
 * DO NOT EDIT
 *
 * This file was automatically generated by
 *   https://github.com/Polymer/gen-typescript-declarations
 *
 * To modify these typings, edit the source file(s):
 *   lib/utils/path.html
 */

/// <reference path="boot.d.ts" />

declare namespace Polymer {

  /**
   * Module with utilities for manipulating structured data path strings.
   */
  namespace Path {


    /**
     * Returns true if the given string is a structured data path (has dots).
     *
     * Example:
     *
     * ```
     * Polymer.Path.isPath('foo.bar.baz') // true
     * Polymer.Path.isPath('foo')         // false
     * ```
     *
     * @returns True if the string contained one or more dots
     */
    function isPath(path: string): boolean;


    /**
     * Returns the root property name for the given path.
     *
     * Example:
     *
     * ```
     * Polymer.Path.root('foo.bar.baz') // 'foo'
     * Polymer.Path.root('foo')         // 'foo'
     * ```
     *
     * @returns Root property name
     */
    function root(path: string): string;


    /**
     * Given `base` is `foo.bar`, `foo` is an ancestor, `foo.bar` is not
     * Returns true if the given path is an ancestor of the base path.
     *
     * Example:
     *
     * ```
     * Polymer.Path.isAncestor('foo.bar', 'foo')         // true
     * Polymer.Path.isAncestor('foo.bar', 'foo.bar')     // false
     * Polymer.Path.isAncestor('foo.bar', 'foo.bar.baz') // false
     * ```
     *
     * @returns True if `path` is an ancestor of `base`.
     */
    function isAncestor(base: string, path: string): boolean;


    /**
     * Given `base` is `foo.bar`, `foo.bar.baz` is an descendant
     *
     * Example:
     *
     * ```
     * Polymer.Path.isDescendant('foo.bar', 'foo.bar.baz') // true
     * Polymer.Path.isDescendant('foo.bar', 'foo.bar')     // false
     * Polymer.Path.isDescendant('foo.bar', 'foo')         // false
     * ```
     *
     * @returns True if `path` is a descendant of `base`.
     */
    function isDescendant(base: string, path: string): boolean;


    /**
     * Replaces a previous base path with a new base path, preserving the
     * remainder of the path.
     *
     * User must ensure `path` has a prefix of `base`.
     *
     * Example:
     *
     * ```
     * Polymer.Path.translate('foo.bar', 'zot', 'foo.bar.baz') // 'zot.baz'
     * ```
     *
     * @returns Translated string
     */
    function translate(base: string, newBase: string, path: string): string;


    /**
     * Converts array-based paths to flattened path.  String-based paths
     * are returned as-is.
     *
     * Example:
     *
     * ```
     * Polymer.Path.normalize(['foo.bar', 0, 'baz'])  // 'foo.bar.0.baz'
     * Polymer.Path.normalize('foo.bar.0.baz')        // 'foo.bar.0.baz'
     * ```
     *
     * @returns Flattened path
     */
    function normalize(path: string|Array<string|number>): string;


    /**
     * Splits a path into an array of property names. Accepts either arrays
     * of path parts or strings.
     *
     * Example:
     *
     * ```
     * Polymer.Path.split(['foo.bar', 0, 'baz'])  // ['foo', 'bar', '0', 'baz']
     * Polymer.Path.split('foo.bar.0.baz')        // ['foo', 'bar', '0', 'baz']
     * ```
     *
     * @returns Array of path parts
     */
    function split(path: string|Array<string|number>): string[];


    /**
     * Reads a value from a path.  If any sub-property in the path is `undefined`,
     * this method returns `undefined` (will never throw.
     *
     * @returns Value at path, or `undefined` if the path could not be
     *  fully dereferenced.
     */
    function get(root: object|null, path: string|Array<string|number>, info?: object|null): any;


    /**
     * Sets a value to a path.  If any sub-property in the path is `undefined`,
     * this method will no-op.
     *
     * @returns The normalized version of the input path
     */
    function set(root: object|null, path: string|Array<string|number>, value: any): string|undefined;
  }
}
