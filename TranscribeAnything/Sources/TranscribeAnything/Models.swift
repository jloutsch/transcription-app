import Foundation

struct AudioFile: Identifiable {
    let id = UUID()
    let url: URL
    var name: String {
        url.lastPathComponent
    }
    var duration: Double?
    var isProcessed: Bool = false
}

struct TranscriptionSettings {
    var modelSize: String = "medium"
    var autoDetectLanguage: Bool = true
    var language: String = "en"
    var enableDiarization: Bool = false
    var diarizationMethod: String = "wavlm"
    var numSpeakers: Int = 2
    var outputPath: String? = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true).first
}

class TranscriptionManager: ObservableObject {
    @Published var audioFiles: [AudioFile] = []
    @Published var settings = TranscriptionSettings()
    @Published var status: String = "Ready"
    @Published var progress: Double = 0.0
    @Published var isTranscribing: Bool = false
    @Published var errorMessage: String?
    @Published var showError: Bool = false

    func startTranscription() {
        // Filter to only unprocessed files
        let unprocessedFiles = audioFiles.filter { !$0.isProcessed }

        guard !unprocessedFiles.isEmpty else {
            status = "No new files to transcribe"
            return
        }

        isTranscribing = true
        status = "Starting transcription..."
        progress = 0.0

        let urls = unprocessedFiles.map { $0.url }
        let fileIDs = unprocessedFiles.map { $0.id }

        PythonBridge.shared.transcribe(
            audioFiles: urls,
            settings: settings,
            progressCallback: { [weak self] prog, message in
                self?.progress = prog
                self?.status = message
            },
            completion: { [weak self] result in
                self?.isTranscribing = false

                switch result {
                case .success(let outputFiles):
                    self?.status = "Transcription complete! Created \(outputFiles.count) file(s)"
                    self?.progress = 1.0
                    // Mark only the transcribed files as processed by ID
                    for i in 0..<(self?.audioFiles.count ?? 0) {
                        if fileIDs.contains(self?.audioFiles[i].id ?? UUID()) {
                            self?.audioFiles[i].isProcessed = true
                        }
                    }
                case .failure(let error):
                    self?.status = "Transcription failed"
                    self?.progress = 0.0
                    self?.showErrorAlert(error: error)
                }
            }
        )
    }

    func clearAll() {
        audioFiles.removeAll()
        status = "Ready"
        progress = 0.0
    }

    func cancelTranscription() {
        PythonBridge.shared.cancelTranscription()
        isTranscribing = false
        status = "Cancelled"
        progress = 0.0
    }

    private func showErrorAlert(error: Error) {
        let errorString = error.localizedDescription

        // Provide user-friendly error messages based on common failure modes
        if errorString.contains("No such file or directory") {
            if errorString.contains("venv") || errorString.contains("python") {
                errorMessage = "Python environment not found. Please ensure the virtual environment is set up at /Users/justin/GitHub/transcription-app/venv"
            } else if errorString.contains("transcribe_cli.py") {
                errorMessage = "Transcription script not found. Please ensure transcribe_cli.py exists in the project directory."
            } else {
                errorMessage = "Could not find required files. Please check that all audio files exist and are accessible."
            }
        } else if errorString.contains("Permission denied") {
            errorMessage = "Permission denied. Please check that you have read access to the audio files and write access to the output directory."
        } else if errorString.contains("ModuleNotFoundError") || errorString.contains("ImportError") {
            errorMessage = "Python dependencies not installed. Please run: source venv/bin/activate && pip install -r requirements.txt"
        } else if errorString.contains("faster-whisper") || errorString.contains("whisper") {
            errorMessage = "Whisper transcription error. The audio file may be corrupted or in an unsupported format."
        } else {
            errorMessage = "Transcription failed: \(errorString)"
        }

        showError = true
    }
}
