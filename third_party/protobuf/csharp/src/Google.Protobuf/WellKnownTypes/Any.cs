// <auto-generated>
//     Generated by the protocol buffer compiler.  DO NOT EDIT!
//     source: google/protobuf/any.proto
// </auto-generated>
#pragma warning disable 1591, 0612, 3021
#region Designer generated code

using pb = global::Google.Protobuf;
using pbc = global::Google.Protobuf.Collections;
using pbr = global::Google.Protobuf.Reflection;
using scg = global::System.Collections.Generic;
namespace Google.Protobuf.WellKnownTypes {

  /// <summary>Holder for reflection information generated from google/protobuf/any.proto</summary>
  public static partial class AnyReflection {

    #region Descriptor
    /// <summary>File descriptor for google/protobuf/any.proto</summary>
    public static pbr::FileDescriptor Descriptor {
      get { return descriptor; }
    }
    private static pbr::FileDescriptor descriptor;

    static AnyReflection() {
      byte[] descriptorData = global::System.Convert.FromBase64String(
          string.Concat(
            "Chlnb29nbGUvcHJvdG9idWYvYW55LnByb3RvEg9nb29nbGUucHJvdG9idWYi",
            "JgoDQW55EhAKCHR5cGVfdXJsGAEgASgJEg0KBXZhbHVlGAIgASgMQm8KE2Nv",
            "bS5nb29nbGUucHJvdG9idWZCCEFueVByb3RvUAFaJWdpdGh1Yi5jb20vZ29s",
            "YW5nL3Byb3RvYnVmL3B0eXBlcy9hbnmiAgNHUEKqAh5Hb29nbGUuUHJvdG9i",
            "dWYuV2VsbEtub3duVHlwZXNiBnByb3RvMw=="));
      descriptor = pbr::FileDescriptor.FromGeneratedCode(descriptorData,
          new pbr::FileDescriptor[] { },
          new pbr::GeneratedClrTypeInfo(null, null, new pbr::GeneratedClrTypeInfo[] {
            new pbr::GeneratedClrTypeInfo(typeof(global::Google.Protobuf.WellKnownTypes.Any), global::Google.Protobuf.WellKnownTypes.Any.Parser, new[]{ "TypeUrl", "Value" }, null, null, null, null)
          }));
    }
    #endregion

  }
  #region Messages
  /// <summary>
  /// `Any` contains an arbitrary serialized protocol buffer message along with a
  /// URL that describes the type of the serialized message.
  ///
  /// Protobuf library provides support to pack/unpack Any values in the form
  /// of utility functions or additional generated methods of the Any type.
  ///
  /// Example 1: Pack and unpack a message in C++.
  ///
  ///     Foo foo = ...;
  ///     Any any;
  ///     any.PackFrom(foo);
  ///     ...
  ///     if (any.UnpackTo(&amp;foo)) {
  ///       ...
  ///     }
  ///
  /// Example 2: Pack and unpack a message in Java.
  ///
  ///     Foo foo = ...;
  ///     Any any = Any.pack(foo);
  ///     ...
  ///     if (any.is(Foo.class)) {
  ///       foo = any.unpack(Foo.class);
  ///     }
  ///
  ///  Example 3: Pack and unpack a message in Python.
  ///
  ///     foo = Foo(...)
  ///     any = Any()
  ///     any.Pack(foo)
  ///     ...
  ///     if any.Is(Foo.DESCRIPTOR):
  ///       any.Unpack(foo)
  ///       ...
  ///
  ///  Example 4: Pack and unpack a message in Go
  ///
  ///      foo := &amp;pb.Foo{...}
  ///      any, err := ptypes.MarshalAny(foo)
  ///      ...
  ///      foo := &amp;pb.Foo{}
  ///      if err := ptypes.UnmarshalAny(any, foo); err != nil {
  ///        ...
  ///      }
  ///
  /// The pack methods provided by protobuf library will by default use
  /// 'type.googleapis.com/full.type.name' as the type URL and the unpack
  /// methods only use the fully qualified type name after the last '/'
  /// in the type URL, for example "foo.bar.com/x/y.z" will yield type
  /// name "y.z".
  ///
  /// JSON
  /// ====
  /// The JSON representation of an `Any` value uses the regular
  /// representation of the deserialized, embedded message, with an
  /// additional field `@type` which contains the type URL. Example:
  ///
  ///     package google.profile;
  ///     message Person {
  ///       string first_name = 1;
  ///       string last_name = 2;
  ///     }
  ///
  ///     {
  ///       "@type": "type.googleapis.com/google.profile.Person",
  ///       "firstName": &lt;string>,
  ///       "lastName": &lt;string>
  ///     }
  ///
  /// If the embedded message type is well-known and has a custom JSON
  /// representation, that representation will be embedded adding a field
  /// `value` which holds the custom JSON in addition to the `@type`
  /// field. Example (for message [google.protobuf.Duration][]):
  ///
  ///     {
  ///       "@type": "type.googleapis.com/google.protobuf.Duration",
  ///       "value": "1.212s"
  ///     }
  /// </summary>
  public sealed partial class Any : pb::IMessage<Any> {
    private static readonly pb::MessageParser<Any> _parser = new pb::MessageParser<Any>(() => new Any());
    private pb::UnknownFieldSet _unknownFields;
    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public static pb::MessageParser<Any> Parser { get { return _parser; } }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public static pbr::MessageDescriptor Descriptor {
      get { return global::Google.Protobuf.WellKnownTypes.AnyReflection.Descriptor.MessageTypes[0]; }
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    pbr::MessageDescriptor pb::IMessage.Descriptor {
      get { return Descriptor; }
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public Any() {
      OnConstruction();
    }

    partial void OnConstruction();

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public Any(Any other) : this() {
      typeUrl_ = other.typeUrl_;
      value_ = other.value_;
      _unknownFields = pb::UnknownFieldSet.Clone(other._unknownFields);
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public Any Clone() {
      return new Any(this);
    }

    /// <summary>Field number for the "type_url" field.</summary>
    public const int TypeUrlFieldNumber = 1;
    private string typeUrl_ = "";
    /// <summary>
    /// A URL/resource name that uniquely identifies the type of the serialized
    /// protocol buffer message. This string must contain at least
    /// one "/" character. The last segment of the URL's path must represent
    /// the fully qualified name of the type (as in
    /// `path/google.protobuf.Duration`). The name should be in a canonical form
    /// (e.g., leading "." is not accepted).
    ///
    /// In practice, teams usually precompile into the binary all types that they
    /// expect it to use in the context of Any. However, for URLs which use the
    /// scheme `http`, `https`, or no scheme, one can optionally set up a type
    /// server that maps type URLs to message definitions as follows:
    ///
    /// * If no scheme is provided, `https` is assumed.
    /// * An HTTP GET on the URL must yield a [google.protobuf.Type][]
    ///   value in binary format, or produce an error.
    /// * Applications are allowed to cache lookup results based on the
    ///   URL, or have them precompiled into a binary to avoid any
    ///   lookup. Therefore, binary compatibility needs to be preserved
    ///   on changes to types. (Use versioned type names to manage
    ///   breaking changes.)
    ///
    /// Note: this functionality is not currently available in the official
    /// protobuf release, and it is not used for type URLs beginning with
    /// type.googleapis.com.
    ///
    /// Schemes other than `http`, `https` (or the empty scheme) might be
    /// used with implementation specific semantics.
    /// </summary>
    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public string TypeUrl {
      get { return typeUrl_; }
      set {
        typeUrl_ = pb::ProtoPreconditions.CheckNotNull(value, "value");
      }
    }

    /// <summary>Field number for the "value" field.</summary>
    public const int ValueFieldNumber = 2;
    private pb::ByteString value_ = pb::ByteString.Empty;
    /// <summary>
    /// Must be a valid serialized protocol buffer of the above specified type.
    /// </summary>
    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public pb::ByteString Value {
      get { return value_; }
      set {
        value_ = pb::ProtoPreconditions.CheckNotNull(value, "value");
      }
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public override bool Equals(object other) {
      return Equals(other as Any);
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public bool Equals(Any other) {
      if (ReferenceEquals(other, null)) {
        return false;
      }
      if (ReferenceEquals(other, this)) {
        return true;
      }
      if (TypeUrl != other.TypeUrl) return false;
      if (Value != other.Value) return false;
      return Equals(_unknownFields, other._unknownFields);
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public override int GetHashCode() {
      int hash = 1;
      if (TypeUrl.Length != 0) hash ^= TypeUrl.GetHashCode();
      if (Value.Length != 0) hash ^= Value.GetHashCode();
      if (_unknownFields != null) {
        hash ^= _unknownFields.GetHashCode();
      }
      return hash;
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public override string ToString() {
      return pb::JsonFormatter.ToDiagnosticString(this);
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public void WriteTo(pb::CodedOutputStream output) {
      if (TypeUrl.Length != 0) {
        output.WriteRawTag(10);
        output.WriteString(TypeUrl);
      }
      if (Value.Length != 0) {
        output.WriteRawTag(18);
        output.WriteBytes(Value);
      }
      if (_unknownFields != null) {
        _unknownFields.WriteTo(output);
      }
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public int CalculateSize() {
      int size = 0;
      if (TypeUrl.Length != 0) {
        size += 1 + pb::CodedOutputStream.ComputeStringSize(TypeUrl);
      }
      if (Value.Length != 0) {
        size += 1 + pb::CodedOutputStream.ComputeBytesSize(Value);
      }
      if (_unknownFields != null) {
        size += _unknownFields.CalculateSize();
      }
      return size;
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public void MergeFrom(Any other) {
      if (other == null) {
        return;
      }
      if (other.TypeUrl.Length != 0) {
        TypeUrl = other.TypeUrl;
      }
      if (other.Value.Length != 0) {
        Value = other.Value;
      }
      _unknownFields = pb::UnknownFieldSet.MergeFrom(_unknownFields, other._unknownFields);
    }

    [global::System.Diagnostics.DebuggerNonUserCodeAttribute]
    public void MergeFrom(pb::CodedInputStream input) {
      uint tag;
      while ((tag = input.ReadTag()) != 0) {
        switch(tag) {
          default:
            _unknownFields = pb::UnknownFieldSet.MergeFieldFrom(_unknownFields, input);
            break;
          case 10: {
            TypeUrl = input.ReadString();
            break;
          }
          case 18: {
            Value = input.ReadBytes();
            break;
          }
        }
      }
    }

  }

  #endregion

}

#endregion Designer generated code
