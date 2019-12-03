﻿#region Copyright notice and license
// Protocol Buffers - Google's data interchange format
// Copyright 2008 Google Inc.  All rights reserved.
// https://developers.google.com/protocol-buffers/
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//     * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//     * Neither the name of Google Inc. nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#endregion

using Google.Protobuf.Collections;
using System;

namespace Google.Protobuf
{
    internal interface IExtensionValue : IEquatable<IExtensionValue>, IDeepCloneable<IExtensionValue>
    {
        void MergeFrom(CodedInputStream input);
        void MergeFrom(IExtensionValue value);
        void WriteTo(CodedOutputStream output);
        int CalculateSize();
    }

    internal sealed class ExtensionValue<T> : IExtensionValue
    {
        private bool hasValue;
        private T field;
        private FieldCodec<T> codec;

        internal ExtensionValue(FieldCodec<T> codec)
        {
            this.codec = codec;
            field = codec.DefaultValue;
        }

        public int CalculateSize()
        {
            if (!hasValue)
            {
                return 0;
            }
            return codec.CalculateSizeWithTag(field);
        }

        public IExtensionValue Clone()
        {
            return new ExtensionValue<T>(codec)
            {
                hasValue = hasValue,
                field = field is IDeepCloneable<T> ? (field as IDeepCloneable<T>).Clone() : field
            };
        }

        public bool Equals(IExtensionValue other)
        {
            if (ReferenceEquals(this, other))
                return true;

            return other is ExtensionValue<T>
                && codec.Equals((other as ExtensionValue<T>).codec)
                && hasValue.Equals((other as ExtensionValue<T>).hasValue)
                && Equals(field, (other as ExtensionValue<T>).field);
            // we check for equality in the codec since we could have equal field values however the values could be written in different ways
        }

        public override int GetHashCode()
        {
            unchecked
            {
                int hash = 17;
                hash = hash * 31 + hasValue.GetHashCode();
                hash = hash * 31 + field.GetHashCode();
                hash = hash * 31 + codec.GetHashCode();
                return hash;
            }
        }

        public void MergeFrom(CodedInputStream input)
        {
            hasValue = true;
            codec.ValueMerger(input, ref field);
        }

        public void MergeFrom(IExtensionValue value)
        {
            if (value is ExtensionValue<T>)
            {
                var extensionValue = value as ExtensionValue<T>;
                if (extensionValue.hasValue)
                {
                    hasValue |= codec.FieldMerger(ref field, extensionValue.field);
                }
            }
        }

        public void WriteTo(CodedOutputStream output)
        {
            if (hasValue)
            {
                output.WriteTag(codec.Tag);
                codec.ValueWriter(output, field);
                if (codec.EndTag != 0)
                {
                    output.WriteTag(codec.EndTag);
                }
            }
        }

        public T GetValue() => field;

        public void SetValue(T value)
        {
            hasValue = true;
            field = value;
        }

        public bool HasValue => hasValue;
    }

    internal sealed class RepeatedExtensionValue<T> : IExtensionValue
    {
        private RepeatedField<T> field;
        private readonly FieldCodec<T> codec;

        internal RepeatedExtensionValue(FieldCodec<T> codec)
        {
            this.codec = codec;
            field = new RepeatedField<T>();
        }

        public int CalculateSize()
        {
            return field.CalculateSize(codec);
        }

        public IExtensionValue Clone()
        {
            return new RepeatedExtensionValue<T>(codec)
            {
                field = field.Clone()
            };
        }

        public bool Equals(IExtensionValue other)
        {
            if (ReferenceEquals(this, other))
                return true;

            return other is RepeatedExtensionValue<T> 
                && field.Equals((other as RepeatedExtensionValue<T>).field) 
                && codec.Equals((other as RepeatedExtensionValue<T>).codec);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                int hash = 17;
                hash = hash * 31 + field.GetHashCode();
                hash = hash * 31 + codec.GetHashCode();
                return hash;
            }
        }

        public void MergeFrom(CodedInputStream input)
        {
            field.AddEntriesFrom(input, codec);
        }

        public void MergeFrom(IExtensionValue value)
        {
            if (value is RepeatedExtensionValue<T>)
            {
                field.Add((value as RepeatedExtensionValue<T>).field);
            }
        }

        public void WriteTo(CodedOutputStream output)
        {
            field.WriteTo(output, codec);
        }

        public RepeatedField<T> GetValue() => field;
    }
}
