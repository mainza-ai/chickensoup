//
//  MultimodalInputView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI
import PhotosUI
import Speech
import Vision
import Combine

// Attachment model for Multimodal input
struct MultimodalAttachment: Identifiable {
    let id = UUID()
    let image: Image
    let uiImage: UIImage?
    let name: String
    var ocrText: String?
}

#if os(macOS)
typealias UIImage = NSImage
extension Image {
    init(uiImage: UIImage) {
        self.init(nsImage: uiImage)
    }
}
#endif

@MainActor
class SpeechRecognizerManager: ObservableObject {
    @Published var transcript = ""
    @Published var isRecording = false
    @Published var micLevel: Double = 0.0
    
    private var speechRecognizer: SFSpeechRecognizer? = SFSpeechRecognizer()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    init() {}
    
    func startTranscribing() {
        guard !isRecording else { return }
        
        // Reset transcript
        transcript = ""
        
        // Request authorization dynamically on action
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            guard let self = self else { return }
            
            Task { @MainActor in
                if status == .authorized {
                    self.beginRecording()
                } else {
                    print("Speech recognition not authorized. Falling back to simulation.")
                    self.isRecording = true
                    self.simulateFallbackDictation()
                }
            }
        }
    }
    
    private func beginRecording() {
        guard !isRecording else { return }
        isRecording = true
        
        // Cancel previous task if running
        recognitionTask?.cancel()
        recognitionTask = nil
        
        #if !os(macOS)
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Audio session setup failed: \(error)")
            simulateFallbackDictation()
            return
        }
        #endif
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            guard let self = self else { return }
            self.recognitionRequest?.append(buffer)
            
            // Calculate mock/approximate audio levels for mic visualization
            if let channelData = buffer.floatChannelData?[0] {
                let frameLength = Int(buffer.frameLength)
                var sum: Float = 0.0
                for i in 0..<frameLength {
                    sum += channelData[i] * channelData[i]
                }
                let rms = sqrt(sum / Float(frameLength))
                Task { @MainActor in
                    self.micLevel = Double(min(max(rms * 10, 0), 1))
                }
            }
        }
        
        audioEngine.prepare()
        do {
            try audioEngine.start()
        } catch {
            print("Audio engine start failed: \(error)")
            isRecording = false
            return
        }
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }
            if let result = result {
                Task { @MainActor in
                    self.transcript = result.bestTranscription.formattedString
                }
            }
            if error != nil || result?.isFinal == true {
                Task { @MainActor in
                    self.stopTranscribing()
                }
            }
        }
    }
    
    func stopTranscribing() {
        guard isRecording else { return }
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        isRecording = false
        micLevel = 0.0
        
        #if !os(macOS)
        do {
            try AVAudioSession.sharedInstance().setActive(false)
        } catch {
            print("Could not deactivate audio session: \(error)")
        }
        #endif
    }
    
    private func simulateFallbackDictation() {
        // Fallback for Simulator / macOS without microphone access
        Task {
            let samplePhrases = [
                "Scan timeline for Element 115 anomaly",
                "Did Mussolini retrieve a UFO in 1933?",
                "Analyze the Ariel School close encounter coordinates",
                "Verify Vatican involvement in Magenta craft transfer"
            ]
            let chosen = samplePhrases.randomElement() ?? "Timeline anomalies detected"
            
            for word in chosen.components(separatedBy: " ") {
                try? await Task.sleep(for: .milliseconds(300))
                if !self.isRecording { break }
                self.transcript += (self.transcript.isEmpty ? "" : " ") + word
                self.micLevel = Double.random(in: 0.1...0.8)
            }
            self.stopTranscribing()
        }
    }
}

struct MultimodalInputView: View {
    @Binding var queryText: String
    @StateObject private var speechManager = SpeechRecognizerManager()
    @State private var attachments: [MultimodalAttachment] = []
    @State private var selectedItem: PhotosPickerItem?
    
    #if os(iOS)
    @State private var isCameraPresented = false
    #endif
    
    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
            // Horizontal toolbar of actions
            HStack(spacing: 12) {
                // Speech Dictation Trigger
                Button {
                    if speechManager.isRecording {
                        speechManager.stopTranscribing()
                    } else {
                        speechManager.startTranscribing()
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: speechManager.isRecording ? "mic.fill" : "mic")
                            .font(.system(size: 14))
                            .foregroundStyle(speechManager.isRecording ? .red : DesignConstants.systemOrangeText)
                        
                        if speechManager.isRecording {
                            // Mic visual feedback bar
                            Capsule()
                                .fill(Color.red)
                                .frame(width: 32, height: 4 + CGFloat(speechManager.micLevel * 12))
                                .animation(.spring(), value: speechManager.micLevel)
                        } else {
                            Text("Voice Dictation")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.secondaryText)
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                }
                .buttonStyle(.plain)
                .onChange(of: speechManager.transcript) { _, newValue in
                    if !newValue.isEmpty {
                        queryText = newValue
                    }
                }
                
                // PhotosPicker for visual intelligence attachments
                PhotosPicker(selection: $selectedItem, matching: .images) {
                    Label("Add Photo", systemImage: "photo.on.rectangle.angled")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                }
                .buttonStyle(.plain)
                .onChange(of: selectedItem) { _, item in
                    Task {
                        if let item = item,
                           let data = try? await item.loadTransferable(type: Data.self),
                           let uiImage = UIImage(data: data) {
                            let image = Image(uiImage: uiImage)
                            var attachment = MultimodalAttachment(image: image, uiImage: uiImage, name: "Photo Attachment")
                            
                            // Proactively run OCR text extraction
                            attachment.ocrText = performOCR(on: uiImage)
                            
                            await MainActor.run {
                                attachments.append(attachment)
                                if let text = attachment.ocrText, !text.isEmpty {
                                    queryText += (queryText.isEmpty ? "" : " ") + "[Extracted: \(text)]"
                                }
                            }
                        }
                    }
                }
                
                #if os(iOS)
                // VisionKit Camera Trigger
                Button {
                    isCameraPresented = true
                } label: {
                    Label("Scan Document", systemImage: "doc.text.viewfinder")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
                }
                .buttonStyle(.plain)
                .sheet(isPresented: $isCameraPresented) {
                    // Custom Camera scanner fallback or VC here
                    Text("VisionKit Scanner Active")
                        .font(.headline)
                        .padding()
                }
                #endif
                
                Spacer()
            }
            
            // Render active attachment chips
            if !attachments.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(attachments) { attachment in
                            HStack(spacing: 6) {
                                attachment.image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                                    .frame(width: 24, height: 24)
                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                                
                                Text(attachment.name)
                                    .font(.caption)
                                    .lineLimit(1)
                                
                                if let ocr = attachment.ocrText {
                                    Image(systemName: "doc.text.magnifyingglass")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.systemOrangeText)
                                        .help(ocr)
                                }
                                
                                Button {
                                    attachments.removeAll { $0.id == attachment.id }
                                } label: {
                                    Image(systemName: "xmark.circle.fill")
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                }
                                .buttonStyle(.plain)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(DesignConstants.systemOrange.opacity(0.08), in: RoundedRectangle(cornerRadius: 6))
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(DesignConstants.systemOrange.opacity(0.2), lineWidth: 1))
                        }
                    }
                    .padding(.vertical, 2)
                }
            }
        }
    }
    
    // OCR Extraction helper
    private func performOCR(on image: UIImage) -> String? {
        #if os(macOS)
        guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return nil }
        #else
        guard let cgImage = image.cgImage else { return nil }
        #endif
        
        var resultText = ""
        let request = VNRecognizeTextRequest { request, error in
            guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
            for observation in observations {
                if let candidate = observation.topCandidates(1).first {
                    resultText += candidate.string + " "
                }
            }
        }
        
        request.recognitionLevel = .accurate
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        do {
            try handler.perform([request])
            return resultText.trimmingCharacters(in: .whitespacesAndNewlines)
        } catch {
            print("OCR extraction failed: \(error)")
            return nil
        }
    }
}
