#!/usr/bin/env python3
"""Inject a silent-audio keep-alive into the main AppDelegate.

When the app enters the background, a muted looping AVAudioPlayer keeps the
audio session alive, so iOS keeps the process running (UIBackgroundModes
already declares `audio`). The MTProto connection stays up, and incoming
messages are presented through Telegram's existing local-notification path —
WeChat-style background notifications entirely inside the app, no external
push infrastructure required. The keep-alive stops when the app returns to
the foreground.
"""
import sys
import pathlib

src = pathlib.Path(sys.argv[1]) / "submodules/TelegramUI/Sources/AppDelegate.swift"
text = src.read_text()

class_anchor = "@objc(AppDelegate) class AppDelegate: UIResponder, UIApplicationDelegate, PKPushRegistryDelegate, UNUserNotificationCenterDelegate, URLSessionDelegate, URLSessionTaskDelegate {"

keepalive_class = """import AVFoundation

final class KeepAliveAudio {
    static let shared = KeepAliveAudio()
    private var player: AVAudioPlayer?

    func activate() {
        DispatchQueue.global(qos: .utility).async {
            do {
                let session = AVAudioSession.sharedInstance()
                try session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
                try session.setActive(true)
            } catch {
                return
            }
            DispatchQueue.main.async {
                if self.player == nil {
                    guard let data = KeepAliveAudio.silentWavData() else { return }
                    self.player = try? AVAudioPlayer(data: data, fileTypeHint: AVFileType.wav.rawValue)
                    self.player?.numberOfLoops = -1
                    self.player?.volume = 0.01
                    self.player?.prepareToPlay()
                }
                self.player?.play()
            }
        }
    }

    func deactivate() {
        DispatchQueue.main.async {
            self.player?.stop()
            self.player = nil
            try? AVAudioSession.sharedInstance().setActive(false, options: [.notifyOthersOnDeactivation])
        }
    }

    // A one-second 8 kHz 16-bit mono silent WAV, generated in code so the
    // bundle needs no extra resource.
    private static func silentWavData() -> Data? {
        let sampleRate = 8000
        let numSamples = 8000
        let dataSize = numSamples * 2
        var data = Data()
        func le32(_ v: UInt32) -> Data { withUnsafeBytes(of: v.littleEndian) { Data($0) } }
        func le16(_ v: UInt16) -> Data { withUnsafeBytes(of: v.littleEndian) { Data($0) } }
        data.append("RIFF".data(using: .ascii)!); data.append(le32(UInt32(36 + dataSize))); data.append("WAVE".data(using: .ascii)!)
        data.append("fmt ".data(using: .ascii)!); data.append(le32(16)); data.append(le16(1)); data.append(le16(1))
        data.append(le32(UInt32(sampleRate))); data.append(le32(UInt32(sampleRate * 2))); data.append(le16(2)); data.append(le16(16))
        data.append("data".data(using: .ascii)!); data.append(le32(UInt32(dataSize)))
        data.append(Data(repeating: 0, count: dataSize))
        return data
    }
}

"""

enter_bg = """    func applicationDidEnterBackground(_ application: UIApplication) {
        let _ = (self.sharedContextPromise.get()"""

enter_bg_new = """    func applicationDidEnterBackground(_ application: UIApplication) {
        // Keep-alive: hold a silent audio session so the process (and its
        // MTProto connection) survives in the background; incoming messages
        // are then presented as local notifications.
        KeepAliveAudio.shared.activate()
        let _ = (self.sharedContextPromise.get()"""

enter_fg = """    func applicationWillEnterForeground(_ application: UIApplication) {
        if self.isActiveValue {"""

enter_fg_new = """    func applicationWillEnterForeground(_ application: UIApplication) {
        // Back to the foreground: the keep-alive session is no longer needed.
        KeepAliveAudio.shared.deactivate()
        if self.isActiveValue {"""

for name, target in [("keepalive class", class_anchor), ("didEnterBackground", enter_bg), ("willEnterForeground", enter_fg)]:
    count = text.count(target)
    if count != 1:
        raise SystemExit(f"keepalive patch: anchor {name!r} found {count} times, expected 1")

text = text.replace(class_anchor, keepalive_class + class_anchor)
text = text.replace(enter_bg, enter_bg_new)
text = text.replace(enter_fg, enter_fg_new)

src.write_text(text)
print("keep-alive injected into", src)
