// Person matte for a lesson take, with Apple Vision (macOS only; make_lesson_base.py compiles and runs it).
// Usage: person_matte TAKE > matte.gray
// Writes one grayscale frame (width*height bytes, white = Amitai) per video frame of TAKE to stdout, at the
// take's own size, in presentation order. VNGeneratePersonSegmentationRequest at .accurate looks at each frame
// on its own: fast hands blur and can drop out, a high chair back can show beside the head.
import AVFoundation
import CoreImage
import Foundation
import Vision

func fail(_ message: String) -> Never {
  FileHandle.standardError.write("person_matte: \(message)\n".data(using: .utf8)!)
  exit(1)
}

guard CommandLine.arguments.count == 2 else { fail("usage: person_matte TAKE") }
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard FileManager.default.fileExists(atPath: url.path) else { fail("no such file: \(url.path)") }
let asset = AVURLAsset(url: url)
guard let track = asset.tracks(withMediaType: .video).first else { fail("no video track in \(url.path)") }
let width = Int(track.naturalSize.width), height = Int(track.naturalSize.height)
let reader: AVAssetReader
do { reader = try AVAssetReader(asset: asset) } catch { fail("can't read \(url.path): \(error)") }
let output = AVAssetReaderTrackOutput(
  track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(output)
reader.startReading()

let context = CIContext(options: [.workingColorSpace: NSNull()])
let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
var frame = [UInt8](repeating: 0, count: width * height)
var count = 0
while let sample = output.copyNextSampleBuffer() {
  guard let pixels = CMSampleBufferGetImageBuffer(sample) else { continue }
  do { try VNImageRequestHandler(cvPixelBuffer: pixels, options: [:]).perform([request]) } catch {
    fail("frame \(count): \(error)")
  }
  guard let mask = request.results?.first?.pixelBuffer else { fail("frame \(count): no matte") }
  let image = CIImage(cvPixelBuffer: mask)
  let scaled = image.transformed(
    by: CGAffineTransform(scaleX: CGFloat(width) / image.extent.width, y: CGFloat(height) / image.extent.height))
  context.render(
    scaled, toBitmap: &frame, rowBytes: width, bounds: CGRect(x: 0, y: 0, width: width, height: height),
    format: .L8, colorSpace: nil)
  FileHandle.standardOutput.write(Data(frame))
  count += 1
}
if reader.status == .failed { fail("reading stopped at frame \(count): \(String(describing: reader.error))") }
FileHandle.standardError.write("person_matte: \(count) frames, \(width)x\(height)\n".data(using: .utf8)!)
