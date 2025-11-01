package com.example.sense

import io.flutter.plugin.common.EventChannel

object SmsStreamHandler : EventChannel.StreamHandler {
    private var eventSink: EventChannel.EventSink? = null
    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        eventSink = events
    }
    override fun onCancel(arguments: Any?) {
        eventSink = null
    }
    fun emit(json: String) {
        eventSink?.success(json)
    }
}