package com.example.sense
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Telephony
import android.telephony.SmsMessage
import org.json.JSONObject

class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (Telephony.Sms.Intents.SMS_RECEIVED_ACTION != intent.action) return

        val bundle: Bundle? = intent.extras
        if (bundle == null) return

        @Suppress("DEPRECATION")
        val pdus = bundle.get("pdus") as? Array<*>
        val format = bundle.getString("format")

        if (pdus == null) return

        val fullBody = StringBuilder()
        var sender: String? = null
        val timestampList = mutableListOf<Long>()

        for (pdu in pdus) {
            val msg = SmsMessage.createFromPdu(pdu as ByteArray, format)
            if (sender == null) sender = msg.originatingAddress
            fullBody.append(msg.messageBody)
            timestampList.add(msg.timestampMillis)
        }

        val body = fullBody.toString()
        val ts = timestampList.minOrNull() ?: System.currentTimeMillis()
        if (!isDisasterAlert(body)) return
        val payload = JSONObject().apply {
            put("sender", sender ?: "")
            put("body", body)
            put("timestamp", ts)
        }

        SmsStreamHandler.emit(payload.toString())
    }

    private fun isDisasterAlert(text: String): Boolean {
        val keywords = listOf(
            "재난", "긴급", "대피", "지진", "경보", "호우", "폭우", "화재",
            "[행안부]", "[안전안내]", "특보", "대응요령"
        )
        return keywords.any { text.contains(it) }
    }
}
