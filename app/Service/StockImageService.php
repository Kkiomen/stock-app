<?php

namespace App\Service;

use App\Core\Service\AbstractService;
use App\Models\StockImage;
use Illuminate\Database\Eloquent\Model;

class StockImageService extends AbstractService
{
    const MODEL = StockImage::class;

    public function __construct(
        private ImageService $imageService
    ){}

    /**
     * Save a model instance or create a new one if it doesn't exist.
     * @param Model|null $model
     * @param array|null $data
     * @return Model
     */
    public function save(?Model $model = null, ?array $data = null): Model
    {
        $uploadedImageData = $this->imageService->saveImageByBase64($data['type'], $data['base64']);

        $preparedData = [
            'stock_id' => $data['stock_id'],
            'uuid' => $data['uuid'],
            'date' => now(),
            'type' => $data['type'],
            'dir' => $uploadedImageData['dir'],
            'image' => $uploadedImageData['filename']
        ];

        $model = null;
        return parent::save($model, $preparedData);
    }
}
