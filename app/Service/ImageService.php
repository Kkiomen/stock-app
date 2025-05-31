<?php

namespace App\Service;

use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class ImageService
{
    public function saveImageByBase64(string $type, string $base64): array
    {
        $imageData = base64_decode($base64);

        if (preg_match('/^data:image\/(\w+);base64,/', $imageData, $type)) {
            $imageData = substr($imageData, strpos($imageData, ',') + 1);
            $extension = strtolower($type[1]); // jpg, png, gif, etc.
        } else {
            $extension = 'png';
        }

        $filename = Str::uuid() . '.' . $extension;
        Storage::disk('public')->put("images/{$filename}", $imageData);

        return [
            'dir' => null,
            'filename' => $filename,
        ];
    }
}
