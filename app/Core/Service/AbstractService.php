<?php

namespace App\Core\Service;

use Illuminate\Database\Eloquent\Model;

abstract class AbstractService
{
    const MODEL = null;

    /**
     * Save a model instance or create a new one if it doesn't exist.
     * @param Model|null $model
     * @param array|null $data
     * @return Model
     */
    public function save(?Model $model = null, ?array $data = null): Model
    {
        $class = static::MODEL;

        if($model === null && !empty($data) && array_key_exists('id', $data)){
           $model = $class::find($data['id']);
        }

        if($model === null){
            $model = new $class();
        }

        if($model->id !== null){
            $model->update($data);
        }else{
            if(!empty($data)){
                $model->fill($data);
                $model->save();
            }else{
                $model->save();
            }
        }


        return $model;
    }

    /**
     * Delete a model instance.
     * @param Model $model
     * @return bool
     */
    public function delete(Model $model): bool
    {
        if ($model->exists) {
            return $model->delete();
        }
        return false;
    }


    /**
     * Find a model instance by its ID.
     * @param int $id
     * @return Model|null
     */
    public function find(int $id): ?Model
    {
        $class = static::MODEL;

        return $class::find($id);
    }

    /**
     * Find a model instance by its UUID.
     * @param string $uuid
     * @return Model|null
     */
    public function findByUuid(string $uuid): ?Model
    {
        $class = static::MODEL;

        return $class::where('uuid', $uuid)->first();
    }

    /**
     * Get all model instances.
     * @return \Illuminate\Database\Eloquent\Collection
     */
    public function all()
    {
        $class = static::MODEL;

        return $class::all();
    }

    /**
     * Get the model instance by its UUID or create a new one if it doesn't exist.
     * @param string $uuid
     * @return Model
     */
    public function getByUuidOrCreate(string $uuid): Model
    {
        $model = $this->findByUuid($uuid);

        if ($model === null) {
            $class = static::MODEL;
            $model = new $class();
            $model->uuid = $uuid;
            $model->save();
        }

        return $model;
    }
}
