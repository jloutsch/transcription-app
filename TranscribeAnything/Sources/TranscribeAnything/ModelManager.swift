import Foundation
import SwiftUI

struct ModelInfo: Identifiable, Equatable {
    let id: String
    let name: String
    let displayName: String
    let size: String
    let speed: String
    let accuracy: String
    let description: String
    let approximateSize: Int64 // in MB
    let isDistilled: Bool // Whether this is a Distil-Whisper model

    var isDownloaded: Bool {
        ModelManager.shared.isModelDownloaded(id)
    }

    static func == (lhs: ModelInfo, rhs: ModelInfo) -> Bool {
        lhs.id == rhs.id
    }
}

class ModelManager: ObservableObject {
    static let shared = ModelManager()

    @Published var downloadProgress: [String: Double] = [:]
    @Published var isDownloading: [String: Bool] = [:]

    let availableModels: [ModelInfo] = [
        // Standard Whisper Models
        ModelInfo(
            id: "tiny",
            name: "tiny",
            displayName: "Whisper Tiny",
            size: "~75 MB",
            speed: "Very Fast",
            accuracy: "Basic",
            description: "Best for real-time transcription or when speed is critical.",
            approximateSize: 75,
            isDistilled: false
        ),
        ModelInfo(
            id: "base",
            name: "base",
            displayName: "Whisper Base",
            size: "~145 MB",
            speed: "Fast",
            accuracy: "Good",
            description: "Good balance for everyday use. Suitable for podcasts and meetings.",
            approximateSize: 145,
            isDistilled: false
        ),
        ModelInfo(
            id: "small",
            name: "small",
            displayName: "Whisper Small",
            size: "~488 MB",
            speed: "Moderate",
            accuracy: "Very Good",
            description: "Recommended for most users. Excellent balance of speed and accuracy.",
            approximateSize: 488,
            isDistilled: false
        ),
        ModelInfo(
            id: "medium",
            name: "medium",
            displayName: "Whisper Medium",
            size: "~1.5 GB",
            speed: "Slow",
            accuracy: "Excellent",
            description: "High accuracy for challenging audio with accents or background noise.",
            approximateSize: 1500,
            isDistilled: false
        ),
        ModelInfo(
            id: "large-v3",
            name: "large-v3",
            displayName: "Whisper Large v3",
            size: "~3.1 GB",
            speed: "Very Slow",
            accuracy: "Best",
            description: "Latest and most accurate. Improved timestamps and multilingual support.",
            approximateSize: 3100,
            isDistilled: false
        ),

        // Distil-Whisper Models (6x faster alternatives)
        ModelInfo(
            id: "distil-small.en",
            name: "distil-small.en",
            displayName: "Distil-Whisper Small (English)",
            size: "~166 MB",
            speed: "Very Fast",
            accuracy: "Very Good",
            description: "6x faster than Whisper Small with similar accuracy. English only.",
            approximateSize: 166,
            isDistilled: true
        ),
        ModelInfo(
            id: "distil-medium.en",
            name: "distil-medium.en",
            displayName: "Distil-Whisper Medium (English)",
            size: "~400 MB",
            speed: "Fast",
            accuracy: "Excellent",
            description: "6x faster than Whisper Medium. Best speed/accuracy for English.",
            approximateSize: 400,
            isDistilled: true
        ),
        ModelInfo(
            id: "distil-large-v3",
            name: "distil-large-v3",
            displayName: "Distil-Whisper Large v3",
            size: "~1.5 GB",
            speed: "Moderate",
            accuracy: "Best",
            description: "Fastest large model. 6x speed improvement over Whisper Large v3.",
            approximateSize: 1500,
            isDistilled: true
        )
    ]

    private var cacheDirectory: URL {
        let home = FileManager.default.homeDirectoryForCurrentUser
        return home.appendingPathComponent(".cache/huggingface/hub")
    }

    func isModelDownloaded(_ modelId: String) -> Bool {
        // Check if model exists in Hugging Face cache
        let modelPatterns: [String]

        if modelId.hasPrefix("distil-") {
            // Distil-Whisper models are from distil-whisper organization
            modelPatterns = [
                "models--distil-whisper--\(modelId)",
                "models--Systran--faster-\(modelId)"
            ]
        } else {
            // Standard Whisper models
            modelPatterns = [
                "models--Systran--faster-whisper-\(modelId)"
            ]
        }

        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: cacheDirectory,
            includingPropertiesForKeys: nil
        ) else {
            return false
        }

        return modelPatterns.contains { pattern in
            contents.contains { url in
                url.lastPathComponent.contains(pattern)
            }
        }
    }

    func getModelInfo(for modelId: String) -> ModelInfo? {
        availableModels.first { $0.id == modelId }
    }

    func getDownloadedModels() -> [ModelInfo] {
        availableModels.filter { $0.isDownloaded }
    }

    func getWhisperModels() -> [ModelInfo] {
        availableModels.filter { !$0.isDistilled }
    }

    func getDistilWhisperModels() -> [ModelInfo] {
        availableModels.filter { $0.isDistilled }
    }
}
