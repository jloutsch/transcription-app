import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var transcriptionManager = TranscriptionManager()

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HeaderView()

            Divider()

            // Main content area
            HStack(spacing: 0) {
                // Left sidebar - File list
                FileListView(files: $transcriptionManager.audioFiles)
                    .frame(width: 300)

                Divider()

                // Right panel - Settings and controls
                SettingsView(settings: $transcriptionManager.settings, transcriptionManager: transcriptionManager)
                    .frame(minWidth: 400)
            }

            Divider()

            // Bottom status and progress
            StatusView(status: transcriptionManager.status, progress: transcriptionManager.progress)
        }
        .frame(width: 900, height: 700)
        .alert("Transcription Error", isPresented: $transcriptionManager.showError) {
            Button("OK", role: .cancel) {
                transcriptionManager.showError = false
            }
        } message: {
            Text(transcriptionManager.errorMessage ?? "An unknown error occurred")
        }
    }
}

struct HeaderView: View {
    var body: some View {
        HStack {
            Image(systemName: "waveform")
                .font(.title2)
                .foregroundColor(.blue)

            Text("Transcribe Anything")
                .font(.title2)
                .fontWeight(.semibold)

            Spacer()
        }
        .padding()
        .background(Color(NSColor.windowBackgroundColor))
    }
}

struct FileListView: View {
    @Binding var files: [AudioFile]
    @State private var isDragging = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Audio Files")
                .font(.headline)
                .padding(.horizontal)
                .padding(.top)

            if files.isEmpty {
                VStack(spacing: 16) {
                    Spacer()

                    Image(systemName: "arrow.down.doc")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)

                    Text("Drop audio files here")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Button("Browse Files...") {
                        selectFiles()
                    }
                    .buttonStyle(.borderedProminent)

                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [5]))
                        .foregroundColor(isDragging ? .blue : .secondary)
                )
                .padding()
            } else {
                List {
                    ForEach(files) { file in
                        AudioFileRow(file: file)
                    }
                }
                .listStyle(.inset)
            }
        }
        .background(Color(NSColor.controlBackgroundColor))
        .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
            handleDrop(providers: providers)
            return true
        }
    }

    private func selectFiles() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [
            .audio,
            UTType(filenameExtension: "mp3")!,
            UTType(filenameExtension: "wav")!,
            UTType(filenameExtension: "m4a")!,
            UTType(filenameExtension: "mp4")!,
            UTType(filenameExtension: "flac")!
        ]

        if panel.runModal() == .OK {
            for url in panel.urls {
                files.append(AudioFile(url: url))
            }
        }
    }

    private func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
                if let data = item as? Data,
                   let url = URL(dataRepresentation: data, relativeTo: nil) {
                    // Validate file extension
                    let ext = url.pathExtension.lowercased()
                    let allowedExtensions = ["mp3", "wav", "m4a", "mp4", "flac", "aac", "ogg", "wma", "aiff"]

                    if allowedExtensions.contains(ext) {
                        DispatchQueue.main.async {
                            files.append(AudioFile(url: url))
                        }
                    }
                }
            }
        }
    }
}

struct AudioFileRow: View {
    let file: AudioFile

    var body: some View {
        HStack {
            Image(systemName: "music.note")
                .foregroundColor(.blue)

            VStack(alignment: .leading, spacing: 2) {
                Text(file.name)
                    .lineLimit(1)

                if let duration = file.duration {
                    Text(formatDuration(duration))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            if file.isProcessed {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            }
        }
        .padding(.vertical, 4)
    }

    private func formatDuration(_ seconds: Double) -> String {
        let minutes = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", minutes, secs)
    }
}

struct SettingsView: View {
    @Binding var settings: TranscriptionSettings
    @ObservedObject var transcriptionManager: TranscriptionManager
    @AppStorage("rememberOutputPath") private var rememberOutputPath = false
    @AppStorage("savedOutputPath") private var savedOutputPath = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Model Selection
                GroupBox("Model") {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Whisper (Standard)")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        Picker("Whisper Model", selection: $settings.modelSize) {
                            Text("Tiny").tag("tiny")
                            Text("Base").tag("base")
                            Text("Small").tag("small")
                            Text("Medium").tag("medium")
                            Text("Large-v3").tag("large-v3")
                        }
                        .pickerStyle(.segmented)

                        Divider()
                            .padding(.vertical, 4)

                        Text("Distil-Whisper (6x Faster)")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        Picker("Distil-Whisper Model", selection: $settings.modelSize) {
                            Text("Small (EN)").tag("distil-small.en")
                            Text("Medium (EN)").tag("distil-medium.en")
                            Text("Large v3").tag("distil-large-v3")
                        }
                        .pickerStyle(.segmented)

                        Text(modelDescription)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(8)
                }
                .onChange(of: settings.modelSize) { newValue in
                    // Auto-set language to English for English-only models
                    if newValue.hasSuffix(".en") {
                        settings.language = "en"
                        settings.autoDetectLanguage = false
                    }
                }

                // Language Selection
                GroupBox("Language") {
                    VStack(alignment: .leading, spacing: 8) {
                        if isEnglishOnlyModel {
                            HStack {
                                Image(systemName: "info.circle")
                                    .foregroundColor(.secondary)
                                Text("English only (selected model)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        } else {
                            Toggle("Auto-detect language", isOn: $settings.autoDetectLanguage)

                            if !settings.autoDetectLanguage {
                                Picker("Language", selection: $settings.language) {
                                    Text("English").tag("en")
                                    Text("Spanish").tag("es")
                                    Text("French").tag("fr")
                                    Text("German").tag("de")
                                    Text("Chinese").tag("zh")
                                    Text("Japanese").tag("ja")
                                }
                            }
                        }
                    }
                    .padding(8)
                }

                // Output Settings
                GroupBox("Output") {
                    VStack(alignment: .leading, spacing: 8) {
                        Toggle("Remember output location", isOn: $rememberOutputPath)
                            .onChange(of: rememberOutputPath) { newValue in
                                if newValue, let currentPath = settings.outputPath {
                                    savedOutputPath = currentPath
                                } else if !newValue {
                                    savedOutputPath = ""
                                }
                            }

                        HStack {
                            Text("Save to:")
                            Spacer()
                            Button("Choose Folder...") {
                                selectOutputFolder()
                            }
                        }

                        if let path = settings.outputPath {
                            Text(path)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .lineLimit(2)
                        }
                    }
                    .padding(8)
                }

                Spacer()

                // Action Buttons
                HStack {
                    if transcriptionManager.isTranscribing {
                        Button("Cancel") {
                            transcriptionManager.cancelTranscription()
                        }
                        .buttonStyle(.bordered)
                        .tint(.red)
                    } else {
                        Button("Clear All") {
                            transcriptionManager.clearAll()
                        }
                        .buttonStyle(.bordered)
                        .disabled(transcriptionManager.audioFiles.isEmpty)
                    }

                    Spacer()

                    if !transcriptionManager.isTranscribing {
                        Button("Start Transcription") {
                            transcriptionManager.startTranscription()
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                        .disabled(transcriptionManager.audioFiles.isEmpty)
                    } else {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }
                .padding(.vertical)
            }
            .padding()
        }
        .onAppear {
            // Restore saved output path if toggle is enabled
            if rememberOutputPath && !savedOutputPath.isEmpty {
                settings.outputPath = savedOutputPath
            }
        }
    }

    private var isEnglishOnlyModel: Bool {
        settings.modelSize.hasSuffix(".en")
    }

    private var modelDescription: String {
        switch settings.modelSize {
        case "tiny": return "Fastest, least accurate"
        case "base": return "Fast, good for simple audio"
        case "small": return "Balanced speed and accuracy"
        case "medium": return "Slower, more accurate"
        case "large-v3": return "Slowest, most accurate"
        case "distil-small.en": return "6x faster than Small, English only"
        case "distil-medium.en": return "6x faster than Medium, English only"
        case "distil-large-v3": return "6x faster than Large v3, multilingual"
        default: return ""
        }
    }

    private func selectOutputFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false

        if panel.runModal() == .OK, let url = panel.url {
            settings.outputPath = url.path
            if rememberOutputPath {
                savedOutputPath = url.path
            }
        }
    }
}

struct StatusView: View {
    let status: String
    let progress: Double

    var body: some View {
        VStack(spacing: 8) {
            if progress > 0 {
                ProgressView(value: progress)
                    .progressViewStyle(.linear)
            }

            HStack {
                Text(status)
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                if progress > 0 && progress < 1 {
                    Text("\(Int(progress * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }
}

// Preview only works in Xcode
// #Preview {
//     ContentView()
// }
