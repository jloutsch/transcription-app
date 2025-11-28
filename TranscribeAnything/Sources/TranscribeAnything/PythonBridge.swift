import Foundation

class PythonBridge {
    static let shared = PythonBridge()

    private let pythonScriptPath: String
    private var process: Process?

    private init() {
        // Find the Python script - look in parent directory of the app
        let projectPath = "/Users/justin/GitHub/transcription-app"
        self.pythonScriptPath = "\(projectPath)/transcribe_cli.py"
    }

    func transcribe(audioFiles: [URL], settings: TranscriptionSettings, progressCallback: @escaping (Double, String) -> Void, completion: @escaping (Result<[String], Error>) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let results = try self.runPythonTranscription(audioFiles: audioFiles, settings: settings, progressCallback: progressCallback)
                DispatchQueue.main.async {
                    completion(.success(results))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
    }

    private func runPythonTranscription(audioFiles: [URL], settings: TranscriptionSettings, progressCallback: @escaping (Double, String) -> Void) throws -> [String] {
        // Create a temporary JSON file with the transcription request
        let request = TranscriptionRequest(
            audioFiles: audioFiles.map { $0.path },
            modelSize: settings.modelSize,
            language: settings.autoDetectLanguage ? nil : settings.language,
            enableDiarization: settings.enableDiarization,
            diarizationMethod: settings.diarizationMethod,
            numSpeakers: settings.numSpeakers,
            outputPath: settings.outputPath ?? NSHomeDirectory()
        )

        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        let requestData = try encoder.encode(request)

        let tempDir = FileManager.default.temporaryDirectory
        let requestFile = tempDir.appendingPathComponent("transcription_request.json")
        try requestData.write(to: requestFile)

        // Run Python script with venv activation
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")

        // Build command that activates venv and runs the script
        let venvPath = "/Users/justin/GitHub/transcription-app/venv"
        let command = "source '\(venvPath)/bin/activate' && python '\(pythonScriptPath)' --json '\(requestFile.path)'"
        process.arguments = ["-c", command]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        try process.run()

        // Read output asynchronously
        var outputData = Data()
        pipe.fileHandleForReading.readabilityHandler = { fileHandle in
            let data = fileHandle.availableData
            if !data.isEmpty {
                outputData.append(data)
                if let output = String(data: data, encoding: .utf8) {
                    // Parse progress updates
                    self.parseProgress(output: output, callback: progressCallback)
                }
            }
        }

        process.waitUntilExit()

        let outputString = String(data: outputData, encoding: .utf8) ?? ""

        if process.terminationStatus != 0 {
            throw TranscriptionError.pythonError(outputString)
        }

        // Parse the output to get file paths
        return self.parseOutputFiles(output: outputString)
    }

    private func parseProgress(output: String, callback: @escaping (Double, String) -> Void) {
        // Parse progress from Python output
        // Expected format: "PROGRESS:0.45:Processing file 3 of 10"
        let lines = output.split(separator: "\n")
        for line in lines {
            if line.hasPrefix("PROGRESS:") {
                let components = line.split(separator: ":")
                if components.count >= 3,
                   let progress = Double(components[1]) {
                    let message = components[2...].joined(separator: ":")
                    DispatchQueue.main.async {
                        callback(progress, String(message))
                    }
                }
            }
        }
    }

    private func parseOutputFiles(output: String) -> [String] {
        // Parse output file paths from Python output
        var files: [String] = []
        let lines = output.split(separator: "\n")
        for line in lines {
            if line.hasPrefix("OUTPUT:") {
                let path = String(line.dropFirst(7))
                files.append(path)
            }
        }
        return files
    }

    func cancelTranscription() {
        process?.terminate()
        process = nil
    }
}

struct TranscriptionRequest: Codable {
    let audioFiles: [String]
    let modelSize: String
    let language: String?
    let enableDiarization: Bool
    let diarizationMethod: String
    let numSpeakers: Int
    let outputPath: String
}

enum TranscriptionError: Error, LocalizedError {
    case pythonError(String)
    case invalidOutput

    var errorDescription: String? {
        switch self {
        case .pythonError(let message):
            return "Python transcription failed: \(message)"
        case .invalidOutput:
            return "Invalid output from transcription process"
        }
    }
}
