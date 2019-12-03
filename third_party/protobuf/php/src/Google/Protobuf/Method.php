<?php
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/protobuf/api.proto

namespace Google\Protobuf;

use Google\Protobuf\Internal\GPBType;
use Google\Protobuf\Internal\RepeatedField;
use Google\Protobuf\Internal\GPBUtil;

/**
 * Method represents a method of an API interface.
 *
 * Generated from protobuf message <code>google.protobuf.Method</code>
 */
class Method extends \Google\Protobuf\Internal\Message
{
    /**
     * The simple name of this method.
     *
     * Generated from protobuf field <code>string name = 1;</code>
     */
    private $name = '';
    /**
     * A URL of the input message type.
     *
     * Generated from protobuf field <code>string request_type_url = 2;</code>
     */
    private $request_type_url = '';
    /**
     * If true, the request is streamed.
     *
     * Generated from protobuf field <code>bool request_streaming = 3;</code>
     */
    private $request_streaming = false;
    /**
     * The URL of the output message type.
     *
     * Generated from protobuf field <code>string response_type_url = 4;</code>
     */
    private $response_type_url = '';
    /**
     * If true, the response is streamed.
     *
     * Generated from protobuf field <code>bool response_streaming = 5;</code>
     */
    private $response_streaming = false;
    /**
     * Any metadata attached to the method.
     *
     * Generated from protobuf field <code>repeated .google.protobuf.Option options = 6;</code>
     */
    private $options;
    /**
     * The source syntax of this method.
     *
     * Generated from protobuf field <code>.google.protobuf.Syntax syntax = 7;</code>
     */
    private $syntax = 0;

    /**
     * Constructor.
     *
     * @param array $data {
     *     Optional. Data for populating the Message object.
     *
     *     @type string $name
     *           The simple name of this method.
     *     @type string $request_type_url
     *           A URL of the input message type.
     *     @type bool $request_streaming
     *           If true, the request is streamed.
     *     @type string $response_type_url
     *           The URL of the output message type.
     *     @type bool $response_streaming
     *           If true, the response is streamed.
     *     @type \Google\Protobuf\Option[]|\Google\Protobuf\Internal\RepeatedField $options
     *           Any metadata attached to the method.
     *     @type int $syntax
     *           The source syntax of this method.
     * }
     */
    public function __construct($data = NULL) {
        \GPBMetadata\Google\Protobuf\Api::initOnce();
        parent::__construct($data);
    }

    /**
     * The simple name of this method.
     *
     * Generated from protobuf field <code>string name = 1;</code>
     * @return string
     */
    public function getName()
    {
        return $this->name;
    }

    /**
     * The simple name of this method.
     *
     * Generated from protobuf field <code>string name = 1;</code>
     * @param string $var
     * @return $this
     */
    public function setName($var)
    {
        GPBUtil::checkString($var, True);
        $this->name = $var;

        return $this;
    }

    /**
     * A URL of the input message type.
     *
     * Generated from protobuf field <code>string request_type_url = 2;</code>
     * @return string
     */
    public function getRequestTypeUrl()
    {
        return $this->request_type_url;
    }

    /**
     * A URL of the input message type.
     *
     * Generated from protobuf field <code>string request_type_url = 2;</code>
     * @param string $var
     * @return $this
     */
    public function setRequestTypeUrl($var)
    {
        GPBUtil::checkString($var, True);
        $this->request_type_url = $var;

        return $this;
    }

    /**
     * If true, the request is streamed.
     *
     * Generated from protobuf field <code>bool request_streaming = 3;</code>
     * @return bool
     */
    public function getRequestStreaming()
    {
        return $this->request_streaming;
    }

    /**
     * If true, the request is streamed.
     *
     * Generated from protobuf field <code>bool request_streaming = 3;</code>
     * @param bool $var
     * @return $this
     */
    public function setRequestStreaming($var)
    {
        GPBUtil::checkBool($var);
        $this->request_streaming = $var;

        return $this;
    }

    /**
     * The URL of the output message type.
     *
     * Generated from protobuf field <code>string response_type_url = 4;</code>
     * @return string
     */
    public function getResponseTypeUrl()
    {
        return $this->response_type_url;
    }

    /**
     * The URL of the output message type.
     *
     * Generated from protobuf field <code>string response_type_url = 4;</code>
     * @param string $var
     * @return $this
     */
    public function setResponseTypeUrl($var)
    {
        GPBUtil::checkString($var, True);
        $this->response_type_url = $var;

        return $this;
    }

    /**
     * If true, the response is streamed.
     *
     * Generated from protobuf field <code>bool response_streaming = 5;</code>
     * @return bool
     */
    public function getResponseStreaming()
    {
        return $this->response_streaming;
    }

    /**
     * If true, the response is streamed.
     *
     * Generated from protobuf field <code>bool response_streaming = 5;</code>
     * @param bool $var
     * @return $this
     */
    public function setResponseStreaming($var)
    {
        GPBUtil::checkBool($var);
        $this->response_streaming = $var;

        return $this;
    }

    /**
     * Any metadata attached to the method.
     *
     * Generated from protobuf field <code>repeated .google.protobuf.Option options = 6;</code>
     * @return \Google\Protobuf\Internal\RepeatedField
     */
    public function getOptions()
    {
        return $this->options;
    }

    /**
     * Any metadata attached to the method.
     *
     * Generated from protobuf field <code>repeated .google.protobuf.Option options = 6;</code>
     * @param \Google\Protobuf\Option[]|\Google\Protobuf\Internal\RepeatedField $var
     * @return $this
     */
    public function setOptions($var)
    {
        $arr = GPBUtil::checkRepeatedField($var, \Google\Protobuf\Internal\GPBType::MESSAGE, \Google\Protobuf\Option::class);
        $this->options = $arr;

        return $this;
    }

    /**
     * The source syntax of this method.
     *
     * Generated from protobuf field <code>.google.protobuf.Syntax syntax = 7;</code>
     * @return int
     */
    public function getSyntax()
    {
        return $this->syntax;
    }

    /**
     * The source syntax of this method.
     *
     * Generated from protobuf field <code>.google.protobuf.Syntax syntax = 7;</code>
     * @param int $var
     * @return $this
     */
    public function setSyntax($var)
    {
        GPBUtil::checkEnum($var, \Google\Protobuf\Syntax::class);
        $this->syntax = $var;

        return $this;
    }

}

